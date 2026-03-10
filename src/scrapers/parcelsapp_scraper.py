"""
Universal Parcel Tracker — 17track API (officiel) + ParcelsApp fallback.

Utilise la clé API 17track (secrets.toml > [tracking] > seventeen_track_api_key)
pour interroger 3100+ transporteurs mondiaux.

Fallback: ParcelsApp long-polling si 17track indisponible.
"""

import logging
import requests
import os
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


def _get_17track_key() -> str:
    """Charge la clé API 17track depuis st.secrets ou variable d'env."""
    # Streamlit secrets
    try:
        import streamlit as st
        return st.secrets.get("tracking", {}).get("seventeen_track_api_key", "")
    except Exception:
        pass
    # Variable d'environnement fallback
    return os.environ.get("SEVENTEEN_TRACK_API_KEY", "")


_DELIVERED_KEYWORDS = {
    "delivered", "livré", "remis", "distribué", "délivré",
    "remis au destinataire", "delivered to",
}
_PROBLEM_KEYWORDS = {
    "exception", "anomalie", "retourné", "returned", "perdu",
    "lost", "damaged", "endommagé", "customs hold", "retourn",
}
_STATUS_MAP = {
    "delivered": "Livré ✅",
    "out for delivery": "En cours de livraison 🚚",
    "in transit": "En transit 📦",
    "picked up": "Pris en charge",
    "shipment information received": "Informations reçues",
    "exception": "Anomalie ⚠️",
    "returned": "Retourné à l'expéditeur",
    "customs": "En douane",
    "delayed": "Retardé",
}

# 17track carrier codes pour les transporteurs courants
_17TRACK_CARRIERS = {
    "dhl": 2151,           # DHL Express
    "dhl express": 2151,
    "colissimo": 100002,   # La Poste / Colissimo
    "laposte": 100002,
    "chronopost": 100003,  # Chronopost
    "ups": 2,              # UPS
    "fedex": 3,            # FedEx
    "tnt": 6,              # TNT
    "dpd": 8,              # DPD
    "gls": 10,             # GLS
    "mondial relay": 100071, # Mondial Relay
    "mondialrelay": 100071,
    "cainiao": 190089,     # Cainiao (AliExpress)
    "yanwen": 100139,
    "amazon": 100233,
}

# Carriers à essayer en auto-détection (ordre de fréquence)
_CARRIER_PROBE_ORDER = [2151, 100002, 100003, 2, 3, 6, 8, 10, 100071, 190089]


class ParcelsAppScraper(BaseScraper):
    """
    Universal parcel tracker — 17track officiel + ParcelsApp fallback.

    Utilise la clé API 17track (3100+ transporteurs).
    Retourne un dict normalisé compatible avec tous les autres scrapers.
    """

    # 17track v2 official API
    TRACK17_API = "https://api.17track.net/track/v2.2/gettrackinfo"
    TRACK17_REGISTER = "https://api.17track.net/track/v2.2/register"

    PARCELSAPP_API = "https://parcelsapp.com/api/v3/shipments/tracking"
    PARCELSAPP_PAGE = "https://parcelsapp.com/en/tracking/{tracking}"

    def get_tracking(self, tracking_number: str, language: str = "fr") -> Optional[Dict[str, Any]]:
        """
        Get tracking info for any parcel — tries multiple sources.

        Args:
            tracking_number: The parcel tracking number.
            language: Language hint ('fr' or 'en').

        Returns:
            Normalized tracking dict or fallback with tracking link.
        """
        logger.info(f"[Universal] Tracking {tracking_number}")

        # 1. Try 17track (most reliable without auth)
        try:
            result = self._fetch_17track(tracking_number)
            if result and result.get("status") != "error":
                logger.info(f"[Universal] 17track succeeded for {tracking_number}")
                return result
        except Exception as e:
            logger.warning(f"[Universal] 17track failed: {e}")

        # 2. Try ParcelsApp long-polling
        try:
            result = self._fetch_parcelsapp_polling(tracking_number)
            if result and result.get("status") != "error":
                logger.info(f"[Universal] ParcelsApp succeeded for {tracking_number}")
                return result
        except Exception as e:
            logger.warning(f"[Universal] ParcelsApp failed: {e}")

        # 3. Fallback: return link only
        return self._link_only_response(tracking_number)

    def scrape(self, **kwargs) -> List[Dict]:
        raise NotImplementedError("Use get_tracking() for single parcel lookup.")

    # ── Source 1: 17track API officielle ─────────────────────────────────

    def _fetch_17track(self, tracking_number: str, carrier_hint: str = "") -> Optional[Dict[str, Any]]:
        """Interroge l'API officielle 17track v2.2 avec clé API."""
        api_key = _get_17track_key()
        if not api_key:
            logger.warning("[17track] Clé API manquante — verifier secrets.toml [tracking]")
            return None

        headers = {
            "Content-Type": "application/json",
            "17token": api_key,
        }

        # Déterminer le code carrier
        carrier_code = None
        if carrier_hint:
            carrier_code = _17TRACK_CARRIERS.get(carrier_hint.lower())

        # Essayer l'enregistrement avec ou sans carrier
        registered = False
        if carrier_code:
            # Cas 1 : carrier connu
            r = requests.post(self.TRACK17_REGISTER,
                json=[{"number": tracking_number, "carrier": carrier_code}],
                headers=headers, timeout=10)
            if r.json().get("data", {}).get("accepted"):
                registered = True
        
        if not registered:
            # Cas 2 : pas de carrier — essai auto-détection
            r = requests.post(self.TRACK17_REGISTER,
                json=[{"number": tracking_number}],
                headers=headers, timeout=10)
            data_reg = r.json().get("data", {})
            if data_reg.get("accepted"):
                registered = True
            else:
                # Cas 3 : probe parmi les carriers courants
                for cid in _CARRIER_PROBE_ORDER:
                    r = requests.post(self.TRACK17_REGISTER,
                        json=[{"number": tracking_number, "carrier": cid}],
                        headers=headers, timeout=8)
                    if r.json().get("data", {}).get("accepted"):
                        registered = True
                        carrier_code = cid
                        logger.info(f"[17track] Auto-detected carrier {cid} for {tracking_number}")
                        break

        if not registered:
            logger.warning(f"[17track] Impossible d'enregistrer {tracking_number}")
            return None

        # Récupérer les infos de tracking
        payload = [{"number": tracking_number}]
        if carrier_code:
            payload[0]["carrier"] = carrier_code

        resp = requests.post(self.TRACK17_API, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        accepted = (
            data.get("data", {}).get("accepted")
            or data.get("dat", {}).get("accepted")
            or []
        )
        if not accepted:
            logger.warning(f"[17track] Pas de données pour {tracking_number}: {data.get('message', '')}")
            return None

        item = accepted[0]
        track = item.get("track_info", item.get("track", {}))
        latest_status = track.get("latest_status", {})

        # Status
        status_code = latest_status.get("status", track.get("e", 0))
        if isinstance(status_code, str):
            status_text = status_code
        else:
            status_text = _17TRACK_STATUS.get(status_code, latest_status.get("sub_status", "En attente d'informations"))

        # Historique
        history = []
        providers = track.get("tracking", {}).get("providers", [{}])
        events = (providers[0].get("events", []) if providers else []) or track.get("z2", [])
        for ev in events:
            history.append({
                "date": ev.get("time_iso") or ev.get("a") or "",
                "status": ev.get("description") or ev.get("z") or "",
                "location": ev.get("location") or ev.get("c") or "",
            })

        # Carrier
        carrier_info = track.get("shipping_info", {})
        carrier_name = carrier_info.get("carrier") or item.get("fn") or str(carrier_code or "Inconnu")

        est_delivery = (
            track.get("time_metrics", {}).get("estimated_delivery_date", {}).get("from")
            or track.get("b3")
        )

        is_delivered = status_code == 40 or (isinstance(status_code, str) and "delivered" in status_code.lower())

        return {
            "carrier": carrier_name,
            "tracking_number": tracking_number,
            "status": status_text,
            "status_normalized": self._normalize_status(status_text),
            "is_delivered": is_delivered,
            "has_problem": status_code in (50, 60),
            "delivery_date": carrier_info.get("delivery_time") or track.get("b2"),
            "estimated_delivery": est_delivery,
            "origin": carrier_info.get("origin_country") or track.get("od"),
            "destination": carrier_info.get("destination_country") or track.get("dd"),
            "history": history,
            "source": "17track",
            "tracking_url": self.PARCELSAPP_PAGE.format(tracking=tracking_number),
            "scraped_at": datetime.now().isoformat(),
        }

    # ── Source 2: ParcelsApp polling ──────────────────────────────────────

    def _fetch_parcelsapp_polling(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """
        Use ParcelsApp long-polling API (same as browser).
        POST to initiate, then poll GET until .done == True.
        """
        uid = str(uuid.uuid4())
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
            "Origin": "https://parcelsapp.com",
            "Referer": self.PARCELSAPP_PAGE.format(tracking=tracking_number),
        }
        payload = {
            "trackingNumber": tracking_number,
            "uuid": uid,
            "language": "fr",
        }
        resp = requests.post(self.PARCELSAPP_API, json=payload, headers=headers, timeout=12)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("done"):
                shipments = data.get("shipments", [])
                if shipments:
                    return self._parse_parcelsapp_shipment(shipments[0], tracking_number)

        # Poll up to 3x with 3s delay
        for _ in range(3):
            time.sleep(3)
            poll = requests.get(
                self.PARCELSAPP_API,
                params={"uuid": uid, "language": "fr"},
                headers=headers,
                timeout=10,
            )
            if poll.status_code == 200:
                pdata = poll.json()
                if pdata.get("done"):
                    shipments = pdata.get("shipments", [])
                    if shipments:
                        return self._parse_parcelsapp_shipment(shipments[0], tracking_number)

        return None

    def _parse_parcelsapp_shipment(self, shipment: dict, tracking_number: str) -> Dict:
        status_raw = shipment.get("status") or shipment.get("lastStatus") or "Inconnu"
        status_text = status_raw.get("label") if isinstance(status_raw, dict) else str(status_raw)

        carrier = shipment.get("carrier") or shipment.get("carrierName") or "Inconnu"
        if isinstance(carrier, dict):
            carrier = carrier.get("name") or "Inconnu"

        history = []
        for ev in (shipment.get("events") or shipment.get("history") or []):
            loc = ev.get("location") or ""
            if isinstance(loc, dict):
                loc = loc.get("label") or ""
            history.append({
                "date": ev.get("date") or ev.get("time") or "",
                "status": ev.get("description") or ev.get("label") or "",
                "location": loc,
            })

        return {
            "carrier": carrier,
            "tracking_number": tracking_number,
            "status": status_text,
            "status_normalized": self._normalize_status(status_text),
            "is_delivered": self._is_delivered(status_text),
            "has_problem": self._has_problem(status_text),
            "delivery_date": shipment.get("deliveryDate"),
            "estimated_delivery": shipment.get("estimatedDelivery") or shipment.get("eta"),
            "origin": shipment.get("origin"),
            "destination": shipment.get("destination"),
            "history": history,
            "source": "parcelsapp",
            "tracking_url": self.PARCELSAPP_PAGE.format(tracking=tracking_number),
            "scraped_at": datetime.now().isoformat(),
        }

    # ── Fallback ──────────────────────────────────────────────────────────

    def _link_only_response(self, tracking_number: str) -> Dict[str, Any]:
        return {
            "carrier": "Inconnu",
            "tracking_number": tracking_number,
            "status": "Données indisponibles",
            "status_normalized": "Inconnu",
            "is_delivered": False,
            "has_problem": False,
            "delivery_date": None,
            "estimated_delivery": None,
            "origin": None,
            "destination": None,
            "history": [],
            "source": "link_only",
            "tracking_url": self.PARCELSAPP_PAGE.format(tracking=tracking_number),
            "scraped_at": datetime.now().isoformat(),
        }

    # ── Utility ───────────────────────────────────────────────────────────

    @staticmethod
    def _normalize_status(status: str) -> str:
        lower = (status or "").lower().strip()
        for en, fr in _STATUS_MAP.items():
            if en in lower:
                return fr
        return status or "Inconnu"

    @staticmethod
    def _is_delivered(status: str) -> bool:
        lower = (status or "").lower()
        return any(kw in lower for kw in _DELIVERED_KEYWORDS)

    @staticmethod
    def _has_problem(status: str) -> bool:
        lower = (status or "").lower()
        return any(kw in lower for kw in _PROBLEM_KEYWORDS)
