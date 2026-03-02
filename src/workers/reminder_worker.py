"""
ReminderWorker — Automatisation des relances transporteurs.

Tourne en thread background dès le démarrage de Streamlit.
Scanne toutes les 4h les dossiers éligibles et envoie les relances
sans intervention du client.

Règles d'escalade automatique :
    J+7   sans réponse → 🟡 Relance niveau 1
    J+14  sans réponse → 🟠 Relance niveau 2 (escalade)
    J+21  sans réponse → 🔴 Relance niveau 3 (mise en demeure)
"""

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Seuils de relance automatique (en jours)
REMINDER_THRESHOLDS = [
    {"days": 7,  "level": 1, "label": "Relance niveau 1"},
    {"days": 14, "level": 2, "label": "Escalade niveau 2"},
    {"days": 21, "level": 3, "label": "Mise en demeure niveau 3"},
]

# Statuts qui rendent un dossier éligible à la relance automatique
ELIGIBLE_STATUSES = ("submitted", "pending", "waiting_response", "under_review")

# Délai entre chaque scan (4 heures)
SCAN_INTERVAL_SECONDS = 4 * 60 * 60


class ReminderWorker:
    """
    Worker background qui automatise les relances transporteurs.
    Utilise threading natif (pas de dépendance externe).
    """

    _instance: Optional["ReminderWorker"] = None
    _lock = threading.Lock()

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.stats = {
            "last_run": None,
            "total_reminders_sent": 0,
            "last_run_count": 0,
        }

    @classmethod
    def get_instance(cls) -> "ReminderWorker":
        """Singleton — une seule instance par processus."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def start_background(self) -> bool:
        """
        Démarre le worker en arrière-plan (thread daemon).
        Idempotent : ne démarre pas un second thread si déjà actif.

        Returns:
            True si démarré, False si déjà en cours.
        """
        if self._thread and self._thread.is_alive():
            logger.debug("ReminderWorker already running.")
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="ReminderWorker",
            daemon=True,  # Daemon: s'arrête automatiquement avec Streamlit
        )
        self._thread.start()
        logger.info("🤖 ReminderWorker démarré (intervalle: 4h).")
        return True

    def stop(self):
        """Arrête proprement le worker."""
        self._stop_event.set()

    def is_running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    # ── Boucle principale ────────────────────────────────────────────────────

    def _run_loop(self):
        """Boucle infinie: scan immédiat au démarrage, puis toutes les 4h."""
        logger.info("ReminderWorker: premier scan au démarrage.")
        self._scan_and_remind()

        while not self._stop_event.is_set():
            # Attendre 4h (vérification toutes les 60s pour réagir à stop_event)
            for _ in range(SCAN_INTERVAL_SECONDS // 60):
                if self._stop_event.is_set():
                    break
                time.sleep(60)

            if not self._stop_event.is_set():
                self._scan_and_remind()

        logger.info("ReminderWorker: arrêté.")

    # ── Logique de scan ──────────────────────────────────────────────────────

    def _scan_and_remind(self):
        """
        Scanne tous les dossiers éligibles et envoie les relances nécessaires.
        """
        try:
            from src.database.database_manager import get_db_manager
            db = get_db_manager()
            conn = db.get_connection()

            sent_count = 0
            now = datetime.now()

            for threshold in REMINDER_THRESHOLDS:
                cutoff = (now - timedelta(days=threshold["days"])).isoformat()
                level = threshold["level"]

                # Dossiers éligibles :
                # - statut actif
                # - créés avant le seuil de jours
                # - niveau de relance INFÉRIEUR au seuil (pas encore atteint ce niveau)
                # - OR : dernier suivi avant le seuil (ne pas re-relancer trop vite)
                try:
                    cur = conn.execute(
                        """
                        SELECT id, claim_reference, carrier, client_id, follow_up_level
                        FROM claims
                        WHERE status IN ({})
                          AND follow_up_level < ?
                          AND (
                                last_follow_up_at IS NULL
                                OR last_follow_up_at < ?
                              )
                          AND created_at < ?
                        """.format(",".join("?" * len(ELIGIBLE_STATUSES))),
                        (*ELIGIBLE_STATUSES, level, cutoff, cutoff),
                    )
                    eligible = cur.fetchall()
                except Exception:
                    # PostgreSQL fallback (%s paramstyle)
                    ph = ",".join(["%s"] * len(ELIGIBLE_STATUSES))
                    cur = conn.cursor()
                    cur.execute(
                        f"""
                        SELECT id, claim_reference, carrier, client_id, follow_up_level
                        FROM claims
                        WHERE status IN ({ph})
                          AND follow_up_level < %s
                          AND (last_follow_up_at IS NULL OR last_follow_up_at < %s)
                          AND created_at < %s
                        """,
                        (*ELIGIBLE_STATUSES, level, cutoff, cutoff),
                    )
                    eligible = cur.fetchall()

                for row in eligible:
                    claim_id, claim_ref, carrier, client_id, current_level = row
                    success = self._send_reminder(
                        conn, claim_id, claim_ref, carrier, client_id, level, now
                    )
                    if success:
                        sent_count += 1
                        logger.info(
                            f"✅ Relance auto {level}× envoyée: {claim_ref} ({carrier})"
                        )

            try:
                conn.commit()
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass

            self.stats["last_run"] = now.isoformat()
            self.stats["last_run_count"] = sent_count
            self.stats["total_reminders_sent"] += sent_count

            if sent_count > 0:
                logger.info(f"🤖 ReminderWorker: {sent_count} relance(s) envoyée(s).")
            else:
                logger.debug("ReminderWorker: aucun dossier éligible pour relance.")

        except Exception as e:
            logger.error(f"ReminderWorker scan error: {e}", exc_info=True)

    def _send_reminder(
        self,
        conn,
        claim_id: int,
        claim_ref: str,
        carrier: str,
        client_id: int,
        level: int,
        now: datetime,
    ) -> bool:
        """
        Enregistre la relance en base et envoie l'email au transporteur.
        Returns True si succès.
        """
        try:
            # 1. Mettre à jour le niveau de relance en base
            ts = now.isoformat()
            try:
                conn.execute(
                    """
                    UPDATE claims
                    SET follow_up_level = ?,
                        last_follow_up_at = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (level, ts, ts, claim_id),
                )
            except Exception:
                conn.cursor().execute(
                    """
                    UPDATE claims
                    SET follow_up_level = %s,
                        last_follow_up_at = %s,
                        updated_at = %s
                    WHERE id = %s
                    """,
                    (level, ts, ts, claim_id),
                )

            # 2. Envoyer l'email de relance
            self._send_followup_email(claim_ref, carrier, client_id, level)

            return True

        except Exception as e:
            logger.warning(f"_send_reminder failed for {claim_ref}: {e}")
            return False

    def _send_followup_email(
        self,
        claim_ref: str,
        carrier: str,
        client_id: int,
        level: int,
    ):
        """Envoie l'email de relance avec POD joint si disponible. Silencieux si l'envoi échoue."""
        labels = {
            1: "Relance amiable",
            2: "Escalade — Sans réponse sous 7 jours",
            3: "Mise en demeure — Dernier avis",
        }
        label = labels.get(level, f"Relance niveau {level}")

        try:
            # ── Chercher le dernier POD lié au dossier ──────────────────────────
            pod_info = ""
            try:
                from src.database.database_manager import get_db_manager
                _db = get_db_manager()
                conn2 = _db.get_connection()
                try:
                    rows = conn2.execute(
                        "SELECT attachment_path, attachment_filename FROM email_attachments "
                        "WHERE claim_reference = ? ORDER BY created_at DESC LIMIT 1",
                        (claim_ref,)
                    ).fetchall()
                except Exception:
                    cur3 = conn2.cursor()
                    cur3.execute(
                        "SELECT attachment_path, attachment_filename FROM email_attachments "
                        "WHERE claim_reference = %s ORDER BY created_at DESC LIMIT 1",
                        (claim_ref,)
                    )
                    rows = cur3.fetchall()
                conn2.close()
                if rows:
                    pod_fname = rows[0][1]
                    pod_info = f"\n\ud83d� Pièce jointe POD : {pod_fname}"
                    logger.info(f"POD trouvé pour {claim_ref}: {pod_fname}")
            except Exception as pod_err:
                logger.debug(f"POD lookup skipped for {claim_ref}: {pod_err}")

            # ── Pour niveau 3: générer la mise en demeure PDF ──────────────────
            legal_info = ""
            if level >= 3:
                try:
                    from src.database.database_manager import get_db_manager as _gdb
                    from src.reports.legal_document_generator import LegalDocumentGenerator
                    import pathlib
                    _db2 = _gdb()
                    claim_data = _db2.get_claim(claim_reference=claim_ref)
                    if claim_data:
                        gen = LegalDocumentGenerator()
                        pdf_path = gen.generate_formal_notice(claim_data, output_dir="data/legal_docs")
                        if pdf_path:
                            legal_info = f"\n\ud83d� Mise en demeure générée : {pathlib.Path(pdf_path).name}"
                            logger.info(f"Mise en demeure générée pour {claim_ref}")
                except Exception as legal_err:
                    logger.debug(f"Legal doc generation skipped for {claim_ref}: {legal_err}")

            # ── Envoi de l'email ──────────────────────────────────────────────
            from src.notifications.email_sender import send_admin_notification
            subject = f"[Auto] {label} — {claim_ref} ({carrier})"
            body = (
                f"Relance automatique envoyée par Refundly.ai.\n\n"
                f"Dossier : {claim_ref}\n"
                f"Transporteur : {carrier}\n"
                f"Niveau d'escalade : {level}/3\n"
                f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
                f"{pod_info}{legal_info}"
            )
            send_admin_notification(subject=subject, body=body)
        except Exception as e:
            logger.debug(f"Followup email skipped for {claim_ref}: {e}")

