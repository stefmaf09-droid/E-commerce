"""
ReminderWorker — Automatisation des relances transporteurs.

Tourne en thread background dès le démarrage de Streamlit.
Scanne toutes les 4h les dossiers éligibles et envoie les relances
sans intervention du client.

Règles d'escalade automatique :
    J+7   sans réponse → 🟡 Relance niveau 1 (demande de statut)
    J+14  sans réponse → 🟠 Relance niveau 2 (avertissement)
    J+21  sans réponse → 🔴 Relance niveau 3 (mise en demeure)

31/08/2026 (audit complet) : réécriture pour deux raisons liées.

1) Ce worker se contentait auparavant de notifier l'équipe ADMIN en interne
   (send_admin_notification) — il ne contactait JAMAIS réellement le
   transporteur, malgré le texte produit ("l'IA prépare les documents
   légaux pour vous") qui laisse penser le contraire. La vraie logique
   d'envoi au transporteur existait déjà (src/workers/email_workers.py,
   via EscalationEmailHandler) mais n'était câblée QUE derrière
   FollowUpManager.process_follow_ups() → TaskQueue.add_task(), or
   TaskQueue.process_pending_tasks() (le "consommateur" qui exécuterait
   réellement les tâches empilées) n'est appelé NULLE PART dans le
   projet : les tâches s'accumulaient dans tasks.db sans jamais s'exécuter.
   Ce worker appelle maintenant directement les fonctions d'envoi
   (synchrone, sans passer par cette file jamais consommée).

2) Ce worker lisait la base via get_db_manager() — un singleton qui,
   avant le correctif de src/database/database_manager.py, était une
   variable globale partagée par TOUT le processus Streamlit (donc par
   tous les clients connectés en même temps). Même après ce correctif
   (scoping par session Streamlit), un thread d'arrière-plan comme celui-ci
   n'a justement AUCUNE session Streamlit à qui appartenir — et il a
   besoin de voir les dossiers de TOUS les comptes (Test et Prod), pas
   d'un seul. Il construit donc désormais ses deux connexions explicitement
   (une base Prod, une base Test isolée) au lieu de dépendre de
   get_db_manager().

Sur décision explicite du client (31/08/2026) : en mode Test, l'action est
simulée — le PDF de mise en demeure (niveau 3) est bien généré localement,
l'état du dossier progresse pour la démo, mais AUCUN email n'est réellement
envoyé au transporteur. Seuls les comptes Prod déclenchent un envoi réel.
"""

import logging
import os
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Seuils de relance automatique (en jours)
REMINDER_THRESHOLDS = [
    {"days": 7,  "level": 1, "label": "Relance niveau 1 (demande de statut)"},
    {"days": 14, "level": 2, "label": "Escalade niveau 2 (avertissement)"},
    {"days": 21, "level": 3, "label": "Mise en demeure niveau 3"},
]

# Statuts qui rendent un dossier éligible à la relance automatique
ELIGIBLE_STATUSES = ("submitted", "pending", "waiting_response", "under_review")

# Seuil (jours) avant de contester automatiquement un rejected sans relance
AUTO_CONTEST_AFTER_DAYS = 3  # contester si rejected depuis plus de 3 jours sans relance

# Délai entre chaque scan (4 heures)
SCAN_INTERVAL_SECONDS = 4 * 60 * 60

_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_TEST_DB_PATH = os.path.join(_ROOT_DIR, "data", "test_recours_ecommerce.db")


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
        # Test de connexion DB Prod au démarrage pour diagnostiquer rapidement.
        try:
            from src.database.database_manager import DatabaseManager
            db = DatabaseManager()
            conn = db.get_connection()
            conn.close()
            logger.info("ReminderWorker: connexion DB Prod OK (%s).", db.db_type)
        except Exception as db_err:
            logger.error(
                "ReminderWorker: IMPOSSIBLE de se connecter à la DB Prod. "
                "Les relances automatiques Prod sont désactivées. Erreur: %s", db_err
            )
            self.stats["db_error"] = str(db_err)
            return  # Arrêter le thread si la DB Prod est inaccessible

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
        Scanne les DEUX bases séparément et explicitement (jamais via le
        singleton get_db_manager(), qui n'a pas de sens pour un thread
        d'arrière-plan sans session Streamlit — voir docstring du module) :
        - la base Prod : relances RÉELLES envoyées au transporteur.
        - la base Test (isolée, sqlite) : relances SIMULÉES (aucun envoi
          réel), pour que les comptes de démo/test voient quand même leurs
          dossiers progresser.
        """
        from src.database.database_manager import DatabaseManager

        sent_count = 0

        try:
            prod_db = DatabaseManager()
            sent_count += self._scan_db(prod_db, simulate=False)
        except Exception as e:
            logger.error(f"ReminderWorker: scan PROD échoué: {e}", exc_info=True)

        try:
            if os.path.exists(_TEST_DB_PATH):
                test_db = DatabaseManager(db_path=_TEST_DB_PATH, db_type="sqlite")
                sent_count += self._scan_db(test_db, simulate=True)
            else:
                logger.debug("ReminderWorker: pas de base Test trouvée, scan Test ignoré.")
        except Exception as e:
            logger.error(f"ReminderWorker: scan TEST échoué: {e}", exc_info=True)

        now = datetime.now()
        self.stats["last_run"] = now.isoformat()
        self.stats["last_run_count"] = sent_count
        self.stats["total_reminders_sent"] += sent_count

        if sent_count > 0:
            logger.info(f"🤖 ReminderWorker: {sent_count} relance(s) traitée(s).")
        else:
            logger.debug("ReminderWorker: aucun dossier éligible pour relance.")

    def _scan_db(self, db, simulate: bool) -> int:
        """Scanne UNE base (Prod ou Test) et déclenche les relances dues.

        Args:
            db: instance DatabaseManager explicite (jamais get_db_manager()).
            simulate: True pour la base Test — aucun envoi externe réel.

        Returns:
            Nombre de relances traitées (réelles ou simulées).
        """
        conn = db.get_connection()
        sent_count = 0
        now = datetime.now()

        try:
            for threshold in REMINDER_THRESHOLDS:
                cutoff = (now - timedelta(days=threshold["days"])).isoformat()
                level = threshold["level"]

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
                        db, conn, claim_id, claim_ref, carrier, client_id, level, now, simulate
                    )
                    if success:
                        sent_count += 1
                        tag = "[SIMULÉ - mode TEST]" if simulate else "[RÉEL]"
                        logger.info(
                            f"✅ {tag} Relance auto niveau {level}: {claim_ref} ({carrier})"
                        )

            try:
                conn.commit()
            except Exception:
                pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

        # Contestation auto des dossiers rejected (pas d'envoi externe dans
        # les deux cas, donc pas besoin d'un simulate séparé ici — juste une
        # génération de PDF + changement de statut, sur la base qu'on scanne).
        try:
            self._scan_rejected_without_followup(db)
        except Exception as e:
            logger.error(f"_scan_rejected_without_followup error: {e}", exc_info=True)

        return sent_count

    def _scan_rejected_without_followup(self, db):
        """
        Scanne les dossiers rejected sans aucune relance préalable, sur la
        base `db` fournie explicitement. Si le rejet date de plus de
        AUTO_CONTEST_AFTER_DAYS jours, génère automatiquement une lettre de
        contestation via AppealGenerator et passe le statut en 'appealing'.
        """
        from src.ai.appeal_generator import AppealGenerator
        import pathlib

        conn = db.get_connection()
        now = datetime.now()
        cutoff = (now - timedelta(days=AUTO_CONTEST_AFTER_DAYS)).isoformat()

        try:
            try:
                cur = conn.execute(
                    "SELECT id, claim_reference, carrier, tracking_number, "
                    "amount_requested, ai_reason_key "
                    "FROM claims WHERE status='rejected' "
                    "AND (follow_up_level=0 OR follow_up_level IS NULL) "
                    "AND created_at < ?",
                    (cutoff,)
                )
            except Exception:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, claim_reference, carrier, tracking_number, "
                    "amount_requested, ai_reason_key "
                    "FROM claims WHERE status='rejected' "
                    "AND (follow_up_level=0 OR follow_up_level IS NULL) "
                    "AND created_at < %s",
                    (cutoff,)
                )
            rows = cur.fetchall()

            contested = 0
            for row in rows:
                try:
                    row = dict(row)
                    claim_ref = row['claim_reference']
                    reason_key = row.get('ai_reason_key') or 'default'
                    dispute_data = {
                        'claim_reference': claim_ref,
                        'tracking_number': row.get('tracking_number', 'N/A'),
                        'carrier': row.get('carrier', 'le transporteur'),
                        'amount_requested': row.get('amount_requested', 0),
                    }
                    gen = AppealGenerator()
                    letter_text = gen.generate(dispute_data, reason_key)
                    pdf_bytes = AppealGenerator.generate_pdf(
                        letter_text, f"contestation_{claim_ref}.pdf"
                    )
                    if pdf_bytes:
                        save_dir = pathlib.Path("data/appeals")
                        save_dir.mkdir(parents=True, exist_ok=True)
                        ts = now.strftime("%Y%m%d_%H%M%S")
                        pdf_file = save_dir / f"{ts}_{claim_ref}_auto_contestation.pdf"
                        pdf_file.write_bytes(pdf_bytes)

                    db.update_claim(row['id'], status='appealing')
                    contested += 1
                    logger.info(
                        f"⚖️ Auto-contestation générée pour {claim_ref} "
                        f"(motif: {reason_key})"
                    )
                except Exception as row_err:
                    logger.warning(f"Auto-contest failed for {row.get('claim_reference')}: {row_err}")

            try:
                conn.commit()
            except Exception:
                pass

            if contested > 0:
                logger.info(
                    f"⚖️ ReminderWorker: {contested} dossier(s) rejeté(s) passé(s) en contestation auto."
                )
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _send_reminder(
        self,
        db,
        conn,
        claim_id: int,
        claim_ref: str,
        carrier: str,
        client_id: int,
        level: int,
        now: datetime,
        simulate: bool,
    ) -> bool:
        """
        Déclenche la relance pour UN dossier : envoi réel au transporteur
        (Prod) ou simulation (Test — aucun envoi externe), puis met à jour
        le niveau de relance en base. Returns True si succès.
        """
        try:
            if simulate:
                success = self._simulate_reminder(db, claim_id, claim_ref, carrier, level)
            else:
                success = self._send_real_reminder(claim_id, claim_ref, level)

            if not success:
                return False

            # Mettre à jour le niveau de relance en base (sur la MÊME
            # connexion/instance que celle scannée, pour éviter toute
            # collision d'ID entre la base Test et la base Prod — deux
            # séquences AUTOINCREMENT indépendantes peuvent réutiliser
            # les mêmes entiers).
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

            # Notification interne à l'équipe admin (jamais au transporteur
            # ni au client) — utile même en simulation pour visualiser ce
            # que ferait le worker, clairement étiqueté comme tel.
            self._send_admin_notification(claim_ref, carrier, level, simulate)

            return True

        except Exception as e:
            logger.warning(f"_send_reminder failed for {claim_ref}: {e}")
            return False

    def _send_real_reminder(self, claim_id: int, claim_ref: str, level: int) -> bool:
        """Envoi RÉEL au transporteur (comptes Prod uniquement).

        Appelle directement les fonctions de src/workers/email_workers.py
        (conçues pour être mises en file via TaskQueue, mais cette file
        n'a jamais de consommateur dans ce projet — voir docstring du
        module). Ces fonctions reconstruisent elles-mêmes une
        DatabaseManager() depuis la config globale, ce qui correspond bien
        à la base Prod puisqu'on ne les appelle ici que pour des dossiers
        trouvés dans cette même base Prod.
        """
        from src.database.database_manager import DatabaseManager
        from src.workers.email_workers import (
            execute_status_request, execute_warning, execute_formal_notice,
        )

        db = DatabaseManager()
        claim = db.get_claim(claim_id=claim_id)
        if not claim:
            logger.warning(f"_send_real_reminder: dossier {claim_ref} introuvable en Prod.")
            return False

        try:
            if level == 1:
                execute_status_request(claim)
            elif level == 2:
                execute_warning(claim)
            elif level == 3:
                execute_formal_notice(claim)
            else:
                return False
            return True
        except Exception as e:
            logger.warning(f"Envoi réel transporteur échoué pour {claim_ref} (niveau {level}): {e}")
            return False

    def _simulate_reminder(self, db, claim_id: int, claim_ref: str, carrier: str, level: int) -> bool:
        """Simulation (comptes Test uniquement) : aucun email envoyé au
        transporteur. Le PDF de mise en demeure (niveau 3) est bien généré
        localement — utile pour la démo — mais rien ne part par email.
        """
        try:
            if level == 3:
                claim = db.get_claim(claim_id=claim_id)
                if claim:
                    from src.reports.legal_document_generator import LegalDocumentGenerator
                    gen = LegalDocumentGenerator()
                    country = claim.get('country', 'FR')
                    lang = 'FR' if country == 'FR' else 'EN'
                    pdf_path = gen.generate_formal_notice(
                        claim, lang=lang, output_dir=os.path.join(_ROOT_DIR, "data", "legal_docs", "TEST")
                    )
                    logger.info(f"[SIMULÉ - mode TEST] PDF de mise en demeure généré (non envoyé) : {pdf_path}")
            logger.info(
                f"[SIMULÉ - mode TEST] Relance niveau {level} pour {claim_ref} ({carrier}) — "
                f"aucun email envoyé au transporteur."
            )
            return True
        except Exception as e:
            logger.warning(f"Simulation de relance échouée pour {claim_ref}: {e}")
            # Même en cas d'échec de génération du PDF, on considère la
            # simulation "traitée" pour ne pas bloquer indéfiniment un
            # dossier de démo sur une erreur de génération de document.
            return True

    def _send_admin_notification(self, claim_ref: str, carrier: str, level: int, simulate: bool):
        """Notification interne (jamais au transporteur ni au client).
        Silencieuse si l'envoi échoue."""
        labels = {
            1: "Relance amiable",
            2: "Escalade — Sans réponse sous 7 jours",
            3: "Mise en demeure — Dernier avis",
        }
        label = labels.get(level, f"Relance niveau {level}")
        prefix = "[SIMULÉ - mode TEST] " if simulate else ""

        try:
            from src.notifications.email_sender import send_admin_notification
            subject = f"[Auto] {prefix}{label} — {claim_ref} ({carrier})"
            body = (
                f"{'Relance SIMULÉE (compte Test, aucun envoi réel au transporteur).' if simulate else 'Relance automatique envoyée par Refundly.ai au transporteur.'}\n\n"
                f"Dossier : {claim_ref}\n"
                f"Transporteur : {carrier}\n"
                f"Niveau d'escalade : {level}/3\n"
                f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
            )
            if simulate:
                logger.info(f"[SIMULÉ - mode TEST] Notification admin (non envoyée) : {subject}")
            else:
                send_admin_notification(subject=subject, body=body)
        except Exception as e:
            logger.debug(f"Notification admin ignorée pour {claim_ref}: {e}")
