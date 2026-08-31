# -*- coding: utf-8 -*-
"""
Injecte le logo Refundly.ai en base64 dans toutes les pages.
Utilisé par client_dashboard_main_new.py, auth_functions.py, onboarding_wizard.py
"""
import base64
import io
import os

_LOGO_B64_CACHE: str | None = None


def _autocrop_logo_bytes(raw_bytes: bytes) -> bytes:
    """Recadre automatiquement le PNG du logo sur son contenu réel.

    31/08/2026 : le fichier static/logo_premium.png est un canevas 1024x1024
    dont le logomark + "Refundly.ai" n'occupe qu'une bande centrale d'environ
    808x253px (le reste est du blanc). Sans ce recadrage, augmenter la
    hauteur CSS de l'<img> agrandit surtout cette zone blanche : le logo
    visible ne grossit presque pas. On recadre donc sur la vraie zone
    d'encre (avec une petite marge de sécurité) avant d'encoder en base64,
    pour que "height: Npx" corresponde enfin à du logo réellement visible.

    Retombe silencieusement sur l'image d'origine si Pillow est absent ou
    si le recadrage échoue pour une raison quelconque (jamais bloquant).
    """
    try:
        from PIL import Image
        import numpy as np

        im = Image.open(io.BytesIO(raw_bytes))
        im = im.convert("RGBA")
        arr = np.array(im)
        rgb = arr[:, :, :3]
        alpha = arr[:, :, 3]

        # Un pixel compte comme "contenu" s'il est à la fois suffisamment
        # opaque et pas quasi-blanc. Seuil à 245 (et pas 254/255) car un
        # ImageChops.difference() en comparaison exacte capte le moindre
        # bruit de compression PNG sur tout le canevas (testé : bbox =
        # l'image entière), ce qui ne recadre rien du tout.
        not_white = (rgb < 245).any(axis=2)
        opaque = alpha > 10
        mask = not_white & opaque

        ys, xs = np.where(mask)
        if ys.size == 0 or xs.size == 0:
            return raw_bytes  # image entièrement blanche : rien à recadrer
        bbox = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)

        # Petite marge de respiration autour du contenu détecté (4%).
        pad = max(4, int(0.04 * max(im.size)))
        left, top, right, bottom = bbox
        left = max(0, left - pad)
        top = max(0, top - pad)
        right = min(im.size[0], right + pad)
        bottom = min(im.size[1], bottom + pad)

        cropped = im.crop((left, top, right, bottom))
        out = io.BytesIO()
        cropped.save(out, format="PNG")
        return out.getvalue()
    except Exception:
        return raw_bytes


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
                raw_bytes = f.read()
            if path.endswith(".png"):
                raw_bytes = _autocrop_logo_bytes(raw_bytes)
            b64 = base64.b64encode(raw_bytes).decode()
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
