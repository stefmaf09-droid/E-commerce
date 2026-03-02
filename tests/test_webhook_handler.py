"""
Tests unitaires pour WebhookHandler.

Couvre:
- Validation de signature HMAC-SHA256 (Shopify / AfterShip format)
- Traitement des événements de tracking (Delivered, Lost, Exception)
- Idempotence (même événement deux fois ignoré)
- Payload incomplet rejeté
"""

import json
import hmac
import hashlib
import base64
import pytest
from unittest.mock import MagicMock, patch, call


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """DB manager entièrement mocké — pas d'accès disque."""
    db = MagicMock()
    conn = MagicMock()
    db.get_connection.return_value = conn
    conn.execute.return_value = MagicMock(fetchone=MagicMock(return_value=None))
    conn.commit.return_value = None
    conn.close.return_value = None
    return db, conn


@pytest.fixture
def handler(mock_db):
    """WebhookHandler avec DB mockée."""
    from src.api.webhook_handler import WebhookHandler
    db, conn = mock_db
    wh = WebhookHandler(db_manager=db)
    return wh, db, conn


def make_payload(tracking: str, tag: str) -> dict:
    return {"msg": {"tracking_number": tracking, "tag": tag}}


def make_hmac_header(secret: str, body: bytes) -> str:
    """Génère une signature Shopify (base64 HMAC-SHA256)."""
    sig = hmac.new(secret.encode(), body, hashlib.sha256).digest()
    return base64.b64encode(sig).decode()


# ─────────────────────────────────────────────────────────────
# Tests verify_signature
# ─────────────────────────────────────────────────────────────

class TestVerifySignature:

    def test_valid_signature_base64(self, handler):
        wh, _, _ = handler
        secret = "mysecret"
        body = b'{"test": "payload"}'
        sig = make_hmac_header(secret, body)
        assert wh.verify_signature(body, secret, sig) is True

    def test_invalid_signature(self, handler):
        wh, _, _ = handler
        assert wh.verify_signature(b"body", "secret", "invalidsig") is False

    def test_wrong_secret(self, handler):
        wh, _, _ = handler
        body = b'{"data": "test"}'
        sig = make_hmac_header("correct_secret", body)
        assert wh.verify_signature(body, "wrong_secret", sig) is False

    def test_tampered_body(self, handler):
        wh, _, _ = handler
        body = b'{"amount": 100}'
        sig = make_hmac_header("secret", body)
        tampered = b'{"amount": 999}'
        assert wh.verify_signature(tampered, "secret", sig) is False

    def test_valid_hex_signature(self, handler):
        wh, _, _ = handler
        secret = "hexsecret"
        body = b"test"
        sig_hex = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        assert wh.verify_signature(body, secret, sig_hex) is True


# ─────────────────────────────────────────────────────────────
# Tests handle_tracking_update
# ─────────────────────────────────────────────────────────────

class TestHandleTrackingUpdate:

    def test_missing_tracking_number_returns_false(self, handler):
        wh, db, conn = handler
        result = wh.handle_tracking_update({"msg": {"tag": "Delivered"}})
        assert result is False

    def test_missing_tag_returns_false(self, handler):
        wh, db, conn = handler
        result = wh.handle_tracking_update({"msg": {"tracking_number": "1Z999"}})
        assert result is False

    def test_idempotency_already_processed(self, handler):
        wh, db, conn = handler
        # Simuler: événement déjà en base
        conn.execute.return_value = MagicMock(fetchone=MagicMock(return_value=(1,)))
        result = wh.handle_tracking_update(make_payload("1Z999", "Delivered"))
        assert result is True  # Idempotent: retourne True sans retraiter

    def test_no_claim_for_tracking(self, handler):
        wh, db, conn = handler
        # Idempotency check → not exists, claim lookup → not found
        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=None)),  # idempotency
            MagicMock(fetchone=MagicMock(return_value=None)),  # claim lookup
        ]
        result = wh.handle_tracking_update(make_payload("1Z999", "Delivered"))
        assert result is False

    def test_delivered_event_updates_status(self, handler):
        wh, db, conn = handler
        # payment_status='paid' => pas d'appel bypass sur la ligne 88 du handler
        claim_row = (42, "submitted", "paid", "damaged")
        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=None)),       # idempotency
            MagicMock(fetchone=MagicMock(return_value=claim_row)),  # claim found
            MagicMock(),  # INSERT webhook_event
        ]
        result = wh.handle_tracking_update(make_payload("COL123", "Delivered"))
        assert result is True
        db.update_claim.assert_called_once_with(42, status="under_review", automation_status="automated")

    def test_lost_event_sets_under_review(self, handler):
        wh, db, conn = handler
        # payment_status='paid' => pas de bypass
        claim_row = (10, "submitted", "paid", "lost")
        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=None)),
            MagicMock(fetchone=MagicMock(return_value=claim_row)),
            MagicMock(),
        ]
        result = wh.handle_tracking_update(make_payload("UPS456", "Lost"))
        assert result is True
        db.update_claim.assert_called_once_with(10, status="under_review", automation_status="automated")

    def test_exception_event_requires_action(self, handler):
        wh, db, conn = handler
        claim_row = (7, "submitted", "unpaid", "damaged")
        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=None)),
            MagicMock(fetchone=MagicMock(return_value=claim_row)),
            MagicMock(),
        ]
        result = wh.handle_tracking_update(make_payload("DHL789", "Exception"))
        assert result is True
        db.update_claim.assert_called_once_with(7, status="under_review", automation_status="action_required")

    def test_lost_claim_delivered_triggers_bypass(self, handler):
        """Un colis 'lost' puis 'Delivered' = potentiel bypass.
        Le handler appelle _trigger_bypass_alert 2 fois :
        - ligne  ~65 : status lost + Delivered => rejected
        - ligne  ~88 : Delivered + payment_status unpaid => bypass check
        """
        wh, db, conn = handler
        claim_row = (99, "submitted", "unpaid", "lost")
        conn.execute.side_effect = [
            MagicMock(fetchone=MagicMock(return_value=None)),
            MagicMock(fetchone=MagicMock(return_value=claim_row)),
            MagicMock(),
        ]
        with patch.object(wh, '_trigger_bypass_alert') as mock_bypass:
            result = wh.handle_tracking_update(make_payload("BYPASS001", "Delivered"))
        assert result is True
        # bypass alert appelé au moins 1 fois (la logique l'appelle 2x pour ce cas)
        assert mock_bypass.call_count >= 1
        mock_bypass.assert_any_call(99, "BYPASS001")
        db.update_claim.assert_any_call(99, status="rejected", automation_status="action_required")
