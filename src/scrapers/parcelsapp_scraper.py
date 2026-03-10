"""
Universal Parcel Tracker — 17track + ParcelsApp fallback.

Uses multiple tracking sources in order:
  1. 17track.net public API (no key needed for basic queries)
  2. ParcelsApp long-polling API (no key for initiation)

Supports 600+ carriers: DHL, Colissimo, Chronopost, Mondial Relay,
UPS, FedEx, TNT, GLS, Cainiao, etc.
"""

import logging
import requests
import json
import re
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


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

# 17track status codes → French
_17TRACK_STATUS = {
    0:  "En attente d'informations",
    10: "Informations d'expédition reçues",
    20: "En transit",
    25: "En transit international",
    30: "En cours de livraison 🚚",
    35: "Tentative de livraison échouée",
    40: "Livré ✅",
    50: "Retourné à l'expéditeur",
    60: "Exception / Anomalie ⚠️",
    99: "Expiré",
}


class ParcelsAppScraper(BaseScraper):
    """
    Universal parcel tracker — multi-source, no API key required.

    Tries 17track → ParcelsApp in order.
    Returns a normalized dict compatible with all other scrapers.
    """

    PARCELSAPP_API = "https://parcelsapp.com/api/v3/shipments/tracking"
    PARCELSAPP_PAGE = "https://parcelsapp.com/en/tracking/{tracking}"
    TRACK17_URL = "https://t.17track.net/restapi/track"

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

    # ── Source 1: 17track ─────────────────────────────────────────────────

    def _fetch_17track(self, tracking_number: str) -> Optional[Dict[str, Any]]:
        """Query 17track.net public tracking endpoint."""
        payload = [{"num": tracking_number}]
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://www.17track.net",
            "Referer": f"https://www.17track.net/en/track#nums={tracking_number}",
            "17token": "",
        }
        resp = requests.post(
            self.TRACK17_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        accepted = data.get("dat", {}).get("accepted", [])
        if not accepted:
            return None

        item = accepted[0]
        track_info = item.get("track", {})

        # Status
        status_code = track_info.get("e", 0)
        status_text = _17TRACK_STATUS.get(status_code, track_info.get("z1", "Inconnu"))

        # History
        history = []
        for ev in (track_info.get("z2") or []):
            history.append({
                "date": ev.get("a", ""),
                "status": ev.get("z", ""),
                "location": ev.get("c", ""),
            })

        # Carrier
        carrier_name = item.get("fn") or item.get("fc") or "Inconnu"

        return {
            "carrier": carrier_name,
            "tracking_number": tracking_number,
            "status": status_text,
            "status_normalized": self._normalize_status(status_text),
            "is_delivered": status_code == 40,
            "has_problem": status_code in (50, 60),
            "delivery_date": track_info.get("b2"),
            "estimated_delivery": track_info.get("b3"),
            "origin": track_info.get("od"),
            "destination": track_info.get("dd"),
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
