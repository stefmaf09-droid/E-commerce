# -*- coding: utf-8 -*-
"""
Injecte le logo Refundly.ai en base64 dans toutes les pages.
Utilisé par client_dashboard_main_new.py, auth_functions.py, onboarding_wizard.py
"""
import base64
import os

_LOGO_B64_CACHE: str | None = None


def get_logo_b64() -> str:
    """Retourne le logo en data URI base64 (mis en cache après le premier appel)."""
    global _LOGO_B64_CACHE
    if _LOGO_B64_CACHE:
        return _LOGO_B64_CACHE

    # Cherche le logo dans plusieurs chemins possibles
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "static", "logo_premium.png"),
        os.path.join(os.path.dirname(__file__), "..", "static", "logo_premium.png"),
        os.path.join(os.getcwd(), "static", "logo_premium.png"),
    ]
    for path in candidates:
        path = os.path.normpath(path)
        if os.path.exists(path):
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ext = "jpeg" if path.endswith((".jpg", ".jpeg")) else "png"
            _LOGO_B64_CACHE = f"data:image/{ext};base64,{b64}"
            return _LOGO_B64_CACHE

    # Jamais trouvé — retourne None
    return ""


def logo_img_tag(height: int = 40, style: str = "") -> str:
    """Retourne un tag <img> HTML avec le logo en base64.

    Args:
        height: hauteur en px de l'image
        style: style CSS supplémentaire

    Returns:
        Balise <img> complète ou fallback texte si logo introuvable
    """
    src = get_logo_b64()
    if src:
        return (
            f'<img src="{src}" alt="Refundly.ai" '
            f'style="height:{height}px;width:auto;display:block;{style}">'
        )

    # Fallback CSS si fichier introuvable
    return (
        '<div style="display:inline-flex;align-items:center;gap:8px;'
        'font-size:1.1rem;font-weight:800;color:#111827;">'
        '<div style="width:32px;height:32px;background:linear-gradient(135deg,#00c6ff,#0072ff);'
        'border-radius:9px;display:flex;align-items:center;justify-content:center;'
        'color:white;font-weight:900;font-size:15px;">R</div>'
        'Refundly<span style="color:#0072ff;font-weight:900;">.AI</span>'
        "</div>"
    )
