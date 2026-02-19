"""
Proactive AI agent for existing Refundly clients.

Analyzes the client's current claim situation and generates actionable proposals
that the floating chatbot can display and execute with one click.

Pattern: Propose → Execute → Summarize → Correct
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────────────────────

def analyze_client_situation(client_email: str) -> dict:
    """
    Analyze the client's current state and return action proposals.

    Returns:
        {
          "proposals": [
            {
              "id": str,
              "title": str,
              "description": str,
              "cta": str,          # Button label
              "action": str,       # action key for execute_action()
              "params": dict,
              "urgent": bool,
            }, ...
          ]
        }
    """
    proposals = []

    try:
        from database.database_manager import get_db_manager
        db = get_db_manager()
        conn = db.get_connection()

        # ── Get client_id ─────────────────────────────────────────────────
        cur = conn.cursor()
        cur.execute("SELECT id FROM clients WHERE email = %s", (client_email,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"proposals": []}
        client_id = row[0]

        # ── Claims with upcoming deadlines (≤ 3 days) ─────────────────────
        deadline_threshold = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        cur.execute(
            """
            SELECT id, claim_reference, carrier, amount_requested, response_deadline
            FROM claims
            WHERE client_id = %s
              AND status IN ('submitted','pending','waiting_response')
              AND response_deadline IS NOT NULL
              AND response_deadline <= %s
            LIMIT 5
            """,
            (client_id, deadline_threshold),
        )
        deadline_claims = cur.fetchall()

        if deadline_claims:
            refs = ", ".join(f"**#{r[1]}**" for r in deadline_claims[:3])
            proposals.append({
                "id": "deadline_followup",
                "title": f"{len(deadline_claims)} dossier(s) avec deadline imminente",
                "description": (
                    f"{refs} arrivent à échéance dans moins de 3 jours. "
                    "Refundly peut envoyer automatiquement les relances aux transporteurs."
                ),
                "cta": "Envoyer les relances maintenant",
                "action": "send_followup_emails",
                "params": {"claim_ids": [r[0] for r in deadline_claims]},
                "urgent": True,
            })

        # ── Claims with no response for 14+ days ─────────────────────────
        stale_threshold = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        cur.execute(
            """
            SELECT id, claim_reference, carrier, follow_up_level
            FROM claims
            WHERE client_id = %s
              AND status IN ('submitted','waiting_response')
              AND last_follow_up_at < %s
              AND follow_up_level < 3
            LIMIT 5
            """,
            (client_id, stale_threshold),
        )
        stale_claims = cur.fetchall()

        if stale_claims:
            proposals.append({
                "id": "escalate_stale",
                "title": f"{len(stale_claims)} dossier(s) sans réponse depuis 14+ jours",
                "description": (
                    f"{len(stale_claims)} dossier(s) n'ont reçu aucune réponse transporteur. "
                    "Je peux envoyer un courrier d'escalade automatiquement."
                ),
                "cta": "Escalader maintenant",
                "action": "escalate_claims",
                "params": {"claim_ids": [r[0] for r in stale_claims]},
                "urgent": False,
            })

        # ── Unclaimed disputes (detected but no claim yet) ────────────────
        cur.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(amount_recoverable), 0)
            FROM disputes
            WHERE client_id = %s AND is_claimed = FALSE
            """,
            (client_id,),
        )
        nd_row = cur.fetchone()
        if nd_row and nd_row[0] > 0:
            count, total = nd_row[0], nd_row[1]
            proposals.append({
                "id": "unclaimed_disputes",
                "title": f"{count} litige(s) non réclamé(s) détecté(s)",
                "description": (
                    f"Potentiel de récupération : **{total:.2f} €**. "
                    "Voulez-vous que Refundly soumette automatiquement les réclamations ?"
                ),
                "cta": f"Soumettre les {count} réclamations",
                "action": "submit_claims",
                "params": {"client_id": client_id},
                "urgent": count > 5,
            })

        # ── Payments ready but not yet transferred ─────────────────────────
        cur.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(client_share), 0)
            FROM payments
            WHERE client_id = %s AND payment_status = 'pending'
            """,
            (client_id,),
        )
        pay_row = cur.fetchone()
        if pay_row and pay_row[0] > 0:
            pcount, ptotal = pay_row[0], pay_row[1]
            proposals.append({
                "id": "pending_payments",
                "title": f"{pcount} virement(s) en attente ({ptotal:.2f} €)",
                "description": (
                    f"**{ptotal:.2f} €** vous sont dus sur {pcount} remboursement(s) "
                    "acceptés par les transporteurs. Le virement peut être déclenché maintenant."
                ),
                "cta": "Déclencher le virement",
                "action": "trigger_payment",
                "params": {"client_id": client_id},
                "urgent": True,
            })

        conn.close()

    except Exception as e:
        logger.warning(f"proactive_agent.analyze error for {client_email}: {e}")

    # Filter out previously dismissed proposals
    import streamlit as st
    proposals = [p for p in proposals if not st.session_state.get(f"dismissed_{p['id']}")]

    return {"proposals": proposals}


def execute_action(action: str, params: dict, client_email: str) -> dict:
    """
    Execute a proposed action and return a result dict.

    Returns:
        {"success": bool, "message": str}  or  {"success": False, "error": str}
    """
    try:
        if action == "send_followup_emails":
            return _send_followup_emails(params.get("claim_ids", []), client_email)

        if action == "escalate_claims":
            return _escalate_claims(params.get("claim_ids", []), client_email)

        if action == "submit_claims":
            return _submit_unclaimed(params.get("client_id"), client_email)

        if action == "trigger_payment":
            return _trigger_payment(params.get("client_id"), client_email)

        return {"success": False, "error": f"Action inconnue : {action}"}

    except Exception as e:
        logger.error(f"execute_action({action}) failed: {e}")
        return {"success": False, "error": str(e)}


# ── Action implementations ───────────────────────────────────────────────────

def _send_followup_emails(claim_ids: list, client_email: str) -> dict:
    """Send follow-up emails for deadline-approaching claims."""
    sent = 0
    for cid in claim_ids:
        try:
            from src.automation.claim_automation import ClaimAutomation
            ca = ClaimAutomation()
            ca.send_followup(claim_id=cid, client_email=client_email)
            sent += 1
        except Exception as e:
            logger.warning(f"followup failed for claim {cid}: {e}")

    if sent == 0:
        return {"success": False, "error": "Aucun email n'a pu être envoyé."}
    return {"success": True, "message": f"✅ {sent} relance(s) envoyée(s) avec succès."}


def _escalate_claims(claim_ids: list, client_email: str) -> dict:
    """Escalate stale claims to the next follow-up level."""
    escalated = 0
    for cid in claim_ids:
        try:
            from database.database_manager import get_db_manager
            db = get_db_manager()
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE claims
                SET follow_up_level = follow_up_level + 1,
                    last_follow_up_at = NOW(),
                    updated_at = NOW()
                WHERE id = %s
                """,
                (cid,),
            )
            conn.commit()
            conn.close()
            escalated += 1
        except Exception as e:
            logger.warning(f"escalate failed for {cid}: {e}")

    return {
        "success": escalated > 0,
        "message": f"✅ {escalated} dossier(s) escaladé(s) au niveau supérieur.",
    }


def _submit_unclaimed(client_id, client_email: str) -> dict:
    """Submit all unclaimed disputes as new claims."""
    try:
        from database.database_manager import get_db_manager
        db = get_db_manager()
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT id FROM disputes WHERE client_id = %s AND is_claimed = FALSE",
            (client_id,),
        )
        dispute_ids = [r[0] for r in cur.fetchall()]
        conn.close()

        submitted = 0
        for did in dispute_ids[:10]:  # cap at 10 per action
            try:
                from src.automation.claim_automation import ClaimAutomation
                ca = ClaimAutomation()
                ca.submit_from_dispute(dispute_id=did, client_email=client_email)
                submitted += 1
            except Exception:
                pass

        return {"success": submitted > 0, "message": f"✅ {submitted} réclamation(s) soumise(s)."}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _trigger_payment(client_id, client_email: str) -> dict:
    """Notify admin to process pending client payments."""
    try:
        from src.notifications.email_sender import send_admin_notification
        send_admin_notification(
            subject=f"[Refundly] Virement à déclencher – client {client_email}",
            body=f"Le client {client_email} a demandé le déclenchement de son virement en attente.",
        )
        return {"success": True, "message": "✅ Demande de virement transmise à l'équipe Refundly."}
    except Exception as e:
        return {"success": False, "error": str(e)}
