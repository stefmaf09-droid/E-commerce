"""
Authentication functions for Streamlit dashboards.

This module contains all authentication-related functions including login,
registration, and password reset functionality.
"""

import streamlit as st
import os
import logging

from src.ui.logo import logo_img_tag as _logo_tag

from src.auth.credentials_manager import CredentialsManager
from src.onboarding.onboarding_manager import OnboardingManager

logger = logging.getLogger(__name__)


def authenticate():
    """
    Authentication with 2-column layout: value proposition left, form right.

    Returns:
        bool: True if user is authenticated, False otherwise.
    """
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.client_email = None
        
        # Reconexion automatique (Protection perte F5)
        qp = st.query_params
        if "token" in qp:
            saved_email = qp.get("token")
            from src.auth.password_manager import get_user_role, has_password
            
            # Simple vérification d'existence pour la démo / F5 reload
            if has_password(saved_email):
                st.session_state.authenticated = True
                st.session_state.client_email = saved_email
                st.session_state.role = get_user_role(saved_email)
                st.session_state.show_portal = True

                # 31/08/2026 : distinction test/prod par compte — la
                # reconnexion automatique par token (F5) ne fixait jusqu'ici
                # jamais env_mode, qui retombait donc sur la valeur par
                # défaut "TEST" fixée dans initialize_session(), quel que
                # soit le mode réel du compte. On relit le mode stocké en
                # base pour rester cohérent avec une connexion classique.
                try:
                    from src.database.database_manager import DatabaseManager
                    _client = DatabaseManager().get_client(email=saved_email)
                    st.session_state.env_mode = (
                        (_client.get('account_mode') if _client else None) or 'test'
                    ).upper()
                except Exception:
                    st.session_state.env_mode = "TEST"  # fail-safe

                # Fetch onboarding status securely
                try:
                    from src.onboarding.onboarding_manager import OnboardingManager
                    mgr = OnboardingManager(saved_email)
                    st.session_state.onboarding_complete = mgr.is_onboarding_complete(saved_email)
                except Exception:
                    st.session_state.onboarding_complete = True  # fail-safe


    if not st.session_state.authenticated:
        _inject_auth_css()

        # Initialiser l'état d'affichage
        if "_show_login" not in st.session_state:
            st.session_state._show_login = False

        # ── NAVIGATION HEADER (comme refundly.fr) ────────────────────────
        # 31/08/2026 : le logo paraissait minuscule même à height=220 car le
        # fichier static/logo_premium.png est un canevas carré 1024x1024 dont
        # le vrai logomark n'occupe qu'une bande centrale (~25% de la
        # hauteur) — le reste est du blanc. Monter la hauteur CSS agrandissait
        # surtout ce blanc, pas le logo. Fix à la racine dans src/ui/logo.py
        # (_autocrop_logo_bytes) : l'image est maintenant recadrée sur son
        # contenu réel avant l'encodage base64, donc "height" correspond enfin
        # à du logo visible de bout en bout → plus besoin d'une valeur
        # extrême, une taille de navbar normale suffit et paraîtra nettement
        # plus grande qu'avant. display:flex + align-items:center recentre
        # verticalement au lieu du margin-top négatif fixe précédent.
        _logo_html = _logo_tag(height=72)
        col_logo, col_links, col_start = st.columns([4, 5.5, 2.5])
        with col_logo:
             # 31/08/2026 : pastille colorée derrière l'icône seule (pas le
             # texte "Refundly.ai") — choix validé par l'utilisateur après
             # comparaison avec une carte englobant tout le logo. L'icône
             # occupe ~34% de la largeur du logo recadré (mesuré sur le
             # fichier réel) — la pastille est donc dimensionnée en % du
             # conteneur pour rester alignée quelle que soit la hauteur choisie.
             st.markdown(
                 f'<div style="display:flex; align-items:center; height:100%; padding-left:20px;">'
                 f'<div style="position:relative; display:inline-flex; align-items:center;">'
                 f'<div style="position:absolute; left:-8%; top:50%; transform:translateY(-50%); '
                 f'width:44%; aspect-ratio:1/1; border-radius:50%; '
                 f'background:radial-gradient(circle, #E8F1FF 0%, #DCEAFF 100%); z-index:0;"></div>'
                 f'<div style="position:relative; z-index:1;">{_logo_html}</div>'
                 f'</div></div>',
                 unsafe_allow_html=True
             )

        with col_links:
             # 31/08/2026 : liens texte "Comment ça marche / Fonctionnalités /
             # FAQ" retirés de la barre de nav (demande utilisateur) — le
             # contenu "Comment ça marche ?" est désormais affiché en entier
             # tout en haut de la page (juste après la nav), plus bas dans
             # cette fonction, au lieu d'un simple lien texte ici.
             pass

        with col_start:
             st.markdown('<div style="margin-top:12px;"></div>', unsafe_allow_html=True)
             if st.button("Connexion", type="primary", key="nav_login", use_container_width=True):
                 st.session_state._show_login = True
                 st.session_state._show_register_tab = False
                 st.rerun()

        # ── AFFICHAGE CONDITIONNEL ───────────────────────────────────────
        if st.session_state._show_login:
            # ═══════ PAGE DE CONNEXION ═══════
            st.markdown("<br>", unsafe_allow_html=True)
            _, col_form, _ = st.columns([1.2, 2, 1.2])
            with col_form:
                tab1, tab2 = st.tabs(["🔑 Connexion", "✨ Créer un compte"])
                with tab1:
                    _render_login_form()
                with tab2:
                    _render_registration_form()

                # Bouton retour
                if st.button("← Retour à l'accueil", key="back_to_landing"):
                    st.session_state._show_login = False
                    st.rerun()
        else:
            # ═══════ LANDING PAGE (hero + stats + features) ═══════

            # 31/08/2026 : section "Comment ça marche ?" déplacée tout en
            # haut de la page (demande utilisateur), à l'emplacement des
            # anciens liens texte de la nav ("Comment ça marche" /
            # "Fonctionnalités" / "FAQ", retirés plus haut).
            #
            # 31/08/2026 (suite) : version compactée — la première version
            # (tailles/espacements identiques à la section d'origine, plus
            # bas dans la page) repoussait le slogan "On récupère ton
            # argent à ta place" hors du premier écran visible, ce qui
            # masquait le message expliquant ce que fait le site. Icônes,
            # marges et texte réduits ici pour que la section tienne dans
            # une hauteur raisonnable et laisse le slogan visible juste en
            # dessous sans avoir à scroller autant.
            #
            # 31/08/2026 (audit complet) : le margin-top négatif utilisé
            # ensuite pour resserrer encore l'écart avec la nav (jusqu'à
            # -100px) a été retiré — un test automatisé (Playwright) a
            # démontré qu'il faisait remonter cette section PAR-DESSUS la
            # ligne de la nav, ce qui interceptait les clics sur le bouton
            # "Connexion" (élément juste au-dessus dans le flux) dans
            # certaines conditions. C'est très probablement la cause des
            # clics sur "Connexion" qui semblaient ne rien faire pendant
            # les tests précédents. margin-top repassé à 0 : plus sûr,
            # au prix d'un écart un peu plus visible avec la nav.
            st.markdown("""
<div id="how-it-works" class="how-it-works-section" style="text-align: center; margin: 0 0 16px; scroll-margin-top: 100px;">
  <div style="display:inline-flex; align-items:center; gap:6px; background:#dcfce7; color:#16a34a; padding:4px 14px; border-radius:50px; font-size:0.8rem; font-weight:600; margin-bottom:8px;">
    <span>✓</span> Simple et efficace
  </div>
  <h2 style="font-size: 1.7rem; font-weight: 800; color: #111827; margin: 0 0 4px; letter-spacing: -0.5px;">Comment ça marche ?</h2>
  <p style="color: #6b7280; font-size: 0.9rem; margin-bottom: 18px;">En 4 étapes simples, récupérez l'argent que vous méritez</p>
  <div class="steps-container" style="display: flex; justify-content: space-between; align-items: flex-start; max-width: 780px; margin: 0 auto; position: relative;">
    <!-- Ligne de progression au centre -->
    <div style="position: absolute; top: 28px; left: 10%; right: 10%; height: 2px; background: linear-gradient(90deg, #3b82f6, #a855f7, #f97316, #22c55e); z-index: 0;"></div>
    <!-- Step 1 -->
    <div class="step-item" style="flex: 1; text-align: center; position: relative; z-index: 1; padding: 0 8px;">
      <div style="width: 52px; height: 52px; background: #3b82f6; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);">
        <span style="color: white; font-size: 1.3rem;">✉️</span>
      </div>
      <div style="width: 20px; height: 20px; background: white; border: 2px solid #22c55e; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; font-weight: bold; color: #22c55e; font-size: 0.7rem;">1</div>
      <h4 style="font-weight: 700; color: #111827; margin-bottom: 2px; font-size: 0.85rem;">Connectez votre boutique</h4>
      <p style="font-size: 0.72rem; color: #6b7280; line-height: 1.3; margin:0;">Connectez votre boutique e-commerce pour l'analyse.</p>
    </div>
    <!-- Step 2 -->
    <div class="step-item" style="flex: 1; text-align: center; position: relative; z-index: 1; padding: 0 8px;">
      <div style="width: 52px; height: 52px; background: #a855f7; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; box-shadow: 0 6px 16px rgba(168, 85, 247, 0.4);">
        <span style="color: white; font-size: 1.3rem;">🔍</span>
      </div>
      <div style="width: 20px; height: 20px; background: white; border: 2px solid #22c55e; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; font-weight: bold; color: #22c55e; font-size: 0.7rem;">2</div>
      <h4 style="font-weight: 700; color: #111827; margin-bottom: 2px; font-size: 0.85rem;">Analyse automatique</h4>
      <p style="font-size: 0.72rem; color: #6b7280; line-height: 1.3; margin:0;">Notre IA détecte les litiges automatiquement.</p>
    </div>
    <!-- Step 3 -->
    <div class="step-item" style="flex: 1; text-align: center; position: relative; z-index: 1; padding: 0 8px;">
      <div style="width: 52px; height: 52px; background: #f97316; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; box-shadow: 0 6px 16px rgba(249, 115, 22, 0.4);">
        <span style="color: white; font-size: 1.3rem;">📄</span>
      </div>
      <div style="width: 20px; height: 20px; background: white; border: 2px solid #22c55e; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; font-weight: bold; color: #22c55e; font-size: 0.7rem;">3</div>
      <h4 style="font-weight: 700; color: #111827; margin-bottom: 2px; font-size: 0.85rem;">Réclamation envoyée</h4>
      <p style="font-size: 0.72rem; color: #6b7280; line-height: 1.3; margin:0;">Demande de remboursement légale envoyée.</p>
    </div>
    <!-- Step 4 -->
    <div class="step-item" style="flex: 1; text-align: center; position: relative; z-index: 1; padding: 0 8px;">
      <div style="width: 52px; height: 52px; background: #22c55e; border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; box-shadow: 0 6px 16px rgba(34, 197, 94, 0.4);">
        <span style="color: white; font-size: 1.3rem;">💵</span>
      </div>
      <div style="width: 20px; height: 20px; background: white; border: 2px solid #22c55e; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; font-weight: bold; color: #22c55e; font-size: 0.7rem;">4</div>
      <h4 style="font-weight: 700; color: #111827; margin-bottom: 2px; font-size: 0.85rem;">Argent récupéré</h4>
      <p style="font-size: 0.72rem; color: #6b7280; line-height: 1.3; margin:0;">Remboursement reçu, commission au succès.</p>
    </div>
  </div>
</div>
            """, unsafe_allow_html=True)

            # Floating badges
            st.markdown("""
<div class="floating-badge badge-left" style="animation-delay: 0s;">
  <div class="badge-icon" style="background: #dcfce7;">💰</div>
  <div>
    <div class="badge-title">Remboursement reçu</div>
    <div class="badge-amount">+45,00 € Chronopost</div>
  </div>
</div>
<div class="floating-badge badge-right" style="animation-delay: 1.5s;">
  <div class="badge-icon" style="background: #d1fae5;">✅</div>
  <div>
    <div class="badge-title">Demande approuvée</div>
    <div class="badge-amount">UPS • +89,90 €</div>
  </div>
</div>
            """, unsafe_allow_html=True)

            # Hero
            st.markdown("""
<div class="auth-hero" style="margin-top: 10px; margin-bottom: 20px;">
  <div class="auth-hero-pill" style="background: rgba(13, 148, 136, 0.08); border: 1px solid rgba(13, 148, 136, 0.2); color: #0f766e;">✨ Zéro risque • Commission uniquement sur les remboursements</div>
  <h1 style="font-size: 4.5rem; letter-spacing: -2px; line-height: 1.1;">On récupère <span class="highlight" style="color: #0f766e;">ton argent</span><br>à ta place</h1>
  <p class="subtitle" style="font-size: 1.2rem; margin-top: 24px;">
    Colis perdus, livraisons en retard, colis endommagés... Refundly analyse, détecte et réclame <strong>automatiquement</strong> ce qui vous est dû.
  </p>
</div>
            """, unsafe_allow_html=True)
            
            # CTA Button (Redirect to login)
            st.markdown('<div style="max-width: 400px; margin: 0 auto;">', unsafe_allow_html=True)
            if st.button("Analyser mes expéditions →", key="hero_cta", use_container_width=True, type="primary"):
                st.session_state._show_login = True
                st.session_state._show_register_tab = False # Redirect to Login
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

            # Mini trust badges below button
            st.markdown("""
<div style="display:flex; justify-content:center; gap: 32px; margin-top:24px; font-size:0.85rem; color:#6b7280; font-weight: 500;">
  <span style="display:flex; align-items:center; gap:6px;"><span style="color:#0f766e;">⚡</span> Analyse en 2 minutes</span>
  <span style="display:flex; align-items:center; gap:6px;"><span style="color:#0f766e;">🛡️</span> Données sécurisées</span>
  <span style="display:flex; align-items:center; gap:6px;"><span style="color:#0f766e;">📈</span> +2M€ récupérés</span>
</div>
            """, unsafe_allow_html=True)

            # 3 KPI Cards at the bottom
            st.markdown('<div style="margin-top: 60px;"></div>', unsafe_allow_html=True)
            _, c1, c2, c3, _ = st.columns([1, 2.5, 2.5, 2.5, 1])
            
            with c1:
                st.markdown("""
                <div class="auth-stat-card" style="text-align: left; padding: 24px;">
                  <div style="font-size: 1.5rem; margin-bottom: 8px;">💰</div>
                  <div style="font-size: 2.5rem; font-weight: 800; color: #111827; line-height:1;">127€</div>
                  <div style="font-size: 0.85rem; color: #6b7280; margin-top: 4px;">Montant moyen récupéré</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown("""
                <div class="auth-stat-card" style="text-align: left; padding: 24px;">
                  <div style="font-size: 1.5rem; margin-bottom: 8px;">⚡</div>
                  <div style="font-size: 2.5rem; font-weight: 800; color: #111827; line-height:1;">15 min</div>
                  <div style="font-size: 0.85rem; color: #6b7280; margin-top: 4px;">Temps moyen par demande</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown("""
                <div class="auth-stat-card" style="text-align: left; padding: 24px;">
                  <div style="font-size: 1.5rem; margin-bottom: 8px;">✅</div>
                  <div style="font-size: 2.5rem; font-weight: 800; color: #111827; line-height:1;">94%</div>
                  <div style="font-size: 0.85rem; color: #6b7280; margin-top: 4px;">Taux de succès</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div style="margin-bottom: 80px;"></div>', unsafe_allow_html=True)

            # Trust badges
            st.markdown("""
<div class="trust-badges">
  <div class="trust-badge-item"><span class="icon">⚡</span> Analyse en 2 minutes</div>
  <div class="trust-badge-item"><span class="icon">🔒</span> Données sécurisées</div>
  <div class="trust-badge-item"><span class="icon">📈</span> +2M€ récupérés</div>
</div>
            """, unsafe_allow_html=True)

            # Stats cards
            st.markdown("""
<div class="auth-stats">
  <div class="auth-stat-card">
    <div class="stat-icon">💰</div>
    <div class="stat-value">127€</div>
    <div class="stat-label">Montant moyen récupéré</div>
  </div>
  <div class="auth-stat-card">
    <div class="stat-icon">⚡</div>
    <div class="stat-value">15 min</div>
    <div class="stat-label">Temps moyen par demande</div>
  </div>
  <div class="auth-stat-card">
    <div class="stat-icon">✅</div>
    <div class="stat-value">94%</div>
    <div class="stat-label">Taux de succès</div>
  </div>
</div>
            """, unsafe_allow_html=True)

            # Features grid
            st.markdown("""
<div id="features" class="auth-features" style="scroll-margin-top: 100px;">
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #7c3aed;">🧠</div>
    <h4>IA avancée</h4>
    <p>Détection automatique des opportunités de remboursement sur vos colis.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #0d9488;">🔒</div>
    <h4>100% sécurisé</h4>
    <p>Vos données sont chiffrées et ne sont jamais partagées avec des tiers.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #0284c7;">⏱️</div>
    <h4>Gain de temps</h4>
    <p>Plus besoin de gérer les réclamations manuellement.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #ea580c;">🛡️</div>
    <h4>Zéro risque</h4>
    <p>Pas de remboursement = pas de frais. Vous payez uniquement sur le succès.</p>
  </div>
  <div class="auth-feature-card">
    <div class="auth-feature-icon" style="background: #16a34a;">📊</div>
    <h4>Tableau de bord</h4>
    <p>Suivez tous vos litiges et remboursements en un coup d'œil.</p>
  </div>
</div>

<!-- FAQ SECTION -->
<div id="faq" style="max-width: 800px; margin: 80px auto; padding: 20px; scroll-margin-top: 50px;">
  <h2 style="font-size: 2.5rem; font-weight: 800; color: #111827; text-align: center; margin-bottom: 40px;">Questions fréquentes</h2>
  <div style="background: white; border-radius: 16px; padding: 24px; border: 1px solid #e5e7eb; margin-bottom: 16px;">
    <h4 style="color: #0d9488; margin-bottom: 8px;">Comment Refundly se rémunère-t-il ?</h4>
    <p style="color: #6b7280; font-size: 0.95rem;">Nous travaillons uniquement au succès. Nous prenons une commission sur les remboursements que nous parvenons à récupérer pour vous. Pas de résultat, pas de frais.</p>
  </div>
  <div style="background: white; border-radius: 16px; padding: 24px; border: 1px solid #e5e7eb; margin-bottom: 16px;">
    <h4 style="color: #0d9488; margin-bottom: 8px;">Quels transporteurs sont supportés ?</h4>
    <p style="color: #6b7280; font-size: 0.95rem;">Nous supportons la majorité des acteurs du marché : Colissimo, Chronopost, UPS, DHL, FedEx, TNT, GLS, et bien d'autres.</p>
  </div>
  <div style="background: white; border-radius: 16px; padding: 24px; border: 1px solid #e5e7eb;">
    <h4 style="color: #0d9488; margin-bottom: 8px;">Mes données sont-elles en sécurité ?</h4>
    <p style="color: #6b7280; font-size: 0.95rem;">Oui, nous utilisons un chiffrement de niveau bancaire et nous n'accédons qu'aux données strictement nécessaires pour identifier vos expéditions litigieuses.</p>
  </div>
</div>
            """, unsafe_allow_html=True)

        return False

    return True


def _inject_auth_css():
    """Premium CSS inspired by refundly.fr landing page design."""
    st.markdown(
        """
<style>
/* ===== GLOBAL AUTH PAGE ===== */
html {
    scroll-behavior: smooth;
}
.stApp {
    background: linear-gradient(180deg, #f0fdf9 0%, #ecfeff 30%, #f0f9ff 70%, #eff6ff 100%) !important;
}

/* Force Primary Buttons to be Teal */
div[data-testid="stButton"] button[kind="primary"] {
    background-color: #0f766e !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover {
    background-color: #0d9488 !important;
    box-shadow: 0 4px 12px rgba(13,148,136,0.2) !important;
}

/* Secondary Buttons (e.g. Connexion) to look like text links */
div[data-testid="stButton"] button[kind="secondary"] {
    background-color: transparent !important;
    color: #4b5563 !important;
    border: none !important;
    box-shadow: none !important;
    font-weight: 600 !important;
    transition: color 0.2s !important;
}
div[data-testid="stButton"] button[kind="secondary"]:hover {
    color: #0f766e !important;
    background-color: transparent !important;
}

/* Clean Input Style */
.stTextInput > div > div > input {
    border-radius: 8px !important;
    border: 1px solid #e5e7eb !important;
    padding: 0.5rem 1rem !important;
    background: white !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
}
.stTextInput > div > div > input:focus {
    border-color: #0f766e !important;
    box-shadow: 0 0 0 2px rgba(15,118,110,0.2) !important;
}

/* ===== AUTH NAVBAR ===== */
.auth-navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 0;
    margin-bottom: 8px;
}
.auth-navbar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 1.4rem;
    font-weight: 800;
    color: #111827;
}
.auth-navbar-logo-icon {
    width: 34px;
    height: 34px;
    background: linear-gradient(135deg, #0d9488, #0f766e);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 900;
    font-size: 16px;
}
.auth-navbar-links {
    display: flex;
    gap: 28px;
    font-size: 0.9rem;
    color: #6b7280;
    font-weight: 500;
}
.auth-navbar-links span {
    cursor: pointer;
    transition: color 0.2s;
}
.auth-navbar-links span:hover {
    color: #0d9488;
}

/* ===== HERO SECTION ===== */
.auth-hero {
    text-align: center;
    padding: 40px 20px 20px;
    max-width: 800px;
    margin: 0 auto;
}
.auth-hero-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(13, 148, 136, 0.08);
    border: 1px solid rgba(13, 148, 136, 0.2);
    border-radius: 50px;
    padding: 8px 20px;
    font-size: 0.85rem;
    color: #0d9488;
    font-weight: 600;
    margin-bottom: 24px;
}
.auth-hero h1 {
    font-size: 3.2rem;
    font-weight: 900;
    line-height: 1.15;
    color: #111827;
    margin: 0 0 20px;
    letter-spacing: -1px;
}
.auth-hero h1 .highlight {
    color: #0d9488;
}
.auth-hero .subtitle {
    font-size: 1.05rem;
    color: #6b7280;
    line-height: 1.6;
    max-width: 600px;
    margin: 0 auto 32px;
}

/* ===== TRUST BADGES ===== */
.trust-badges {
    display: flex;
    justify-content: center;
    gap: 32px;
    margin: 20px 0 32px;
    flex-wrap: wrap;
}
.trust-badge-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.88rem;
    color: #6b7280;
}
.trust-badge-item .icon {
    font-size: 1.1rem;
    color: #0d9488;
}

/* ===== KPI STAT CARDS ===== */
.auth-stats {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 24px auto 32px;
    max-width: 720px;
    flex-wrap: wrap;
}
.auth-stat-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 16px;
    padding: 24px 28px;
    min-width: 200px;
    flex: 1;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.2s, box-shadow 0.2s;
}
.auth-stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.auth-stat-card .stat-icon {
    font-size: 1.8rem;
    margin-bottom: 8px;
}
.auth-stat-card .stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: #111827;
    margin: 4px 0;
}
.auth-stat-card .stat-label {
    font-size: 0.82rem;
    color: #9ca3af;
    font-weight: 500;
}

/* ===== FLOATING BADGES ===== */
.floating-badge {
    position: fixed;
    display: flex;
    align-items: center;
    gap: 10px;
    background: white;
    border-radius: 14px;
    padding: 12px 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    font-size: 0.82rem;
    z-index: 10;
    animation: floatBadge 3s ease-in-out infinite;
    border: 1px solid #f3f4f6;
}
.floating-badge .badge-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.floating-badge .badge-title {
    font-weight: 600;
    color: #374151;
    font-size: 0.78rem;
}
.floating-badge .badge-amount {
    color: #0d9488;
    font-weight: 700;
    font-size: 0.82rem;
}
.badge-left {
    left: 3%;
    /* 31/08/2026 : descendu (18% -> 30%) — trop proche du logo agrandi.
       Section "Comment ça marche ?" ensuite compactée (voir plus bas),
       donc pas besoin d'aller aussi loin que le premier réglage (42%). */
    top: 30%;
}
.badge-right {
    right: 3%;
    top: 30%;
}
.badge-bottom-left {
    left: 5%;
    bottom: 25%;
}
@keyframes floatBadge {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-8px); }
}

/* ===== AUTH FORM CARD ===== */
.auth-form-card {
    background: white;
    border-radius: 20px;
    padding: 32px 28px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    border: 1px solid rgba(0,0,0,0.06);
    max-width: 440px;
    margin: 0 auto;
}

/* ===== FEATURES GRID ===== */
.auth-features {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
    max-width: 800px;
    margin: 32px auto;
}
.auth-feature-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 24px 20px;
    text-align: left;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform 0.2s, box-shadow 0.2s;
}
.auth-feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}
.auth-feature-icon {
    width: 44px;
    height: 44px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    margin-bottom: 14px;
    color: white;
}
.auth-feature-card h4 {
    font-size: 0.95rem;
    font-weight: 700;
    color: #111827;
    margin: 0 0 6px;
}
.auth-feature-card p {
    font-size: 0.82rem;
    color: #6b7280;
    line-height: 1.5;
    margin: 0;
}

/* ===== BUTTON OVERRIDE ===== */
.stButton button {
    background: #0f766e !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 12px 28px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 8px rgba(13, 148, 136, 0.25) !important;
}
.stButton button:hover {
    background: #0d9488 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(13, 148, 136, 0.35) !important;
}

/* ===== STREAMLIT OVERRIDES ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Tabs */
[data-testid="stTab"] {
    font-weight: 600 !important;
    color: #6b7280 !important;
}
[data-testid="stTab"][aria-selected="true"] {
    color: #0d9488 !important;
    border-bottom-color: #0d9488 !important;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _render_login_form():
    """Render the login form."""
    st.markdown("### Connexion à votre compte")
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="votre@email.com")
        password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
        submitted = st.form_submit_button("Se connecter", width='stretch')
        
        if submitted:
            # CORRECTION SÉCURITÉ: Email ET password obligatoires
            if not email or not password:
                st.error("⚠️ Veuillez renseigner l'email ET le mot de passe")
                return False

            # SÉCURITÉ: Vérification du mot de passe avec bcrypt
            # Audit du 26/08/2026 (suite) : import normalisé avec le préfixe
            # src. — l'ancienne forme (`from auth.password_manager import`)
            # ne fonctionnait que par effet de bord (un autre module,
            # importé plus tôt, ajoutait src/ à sys.path). Fragile : l'ordre
            # d'import aurait pu changer et faire planter CHAQUE connexion.
            from src.auth.password_manager import verify_client_password, has_password, get_user_role

            # Audit du 26/08/2026 (suite) : cette vérification s'appuyait
            # jusqu'ici sur manager.get_credentials(email), c'est-à-dire sur
            # l'existence d'une ligne dans la table `credentials` (une
            # boutique connectée), pour décider si le compte existe.
            # Depuis la correction du bug des boutiques fantômes (plus
            # aucune ligne credentials n'est créée tant qu'aucune boutique
            # n'est réellement connectée), tout client inscrit SANS
            # boutique se voyait bloqué à la connexion avec "Email non
            # trouvé" — alors même que son compte existe bel et bien (mot
            # de passe défini). La vraie vérification d'existence de
            # compte est has_password(), indépendante de toute boutique.
            if not has_password(email):
                st.error("❌ Email non trouvé. Utilisez l'onglet 'Créer un compte' pour vous inscrire.")
                return False

            # Verify password
            if verify_client_password(email, password):
                # Audit du 26/08/2026 (suite) : repart d'une URL propre à
                # chaque connexion. Sans ça, un `hub_seen=1`/`page=...`
                # laissé par une session précédente dans le même onglet
                # (déconnexion incomplète, poste partagé, test avec
                # plusieurs comptes) empêchait l'écran d'accueil de
                # s'afficher pour CE client alors qu'il en a besoin.
                st.query_params.clear()
                st.session_state.authenticated = True
                st.session_state.client_email = email

                # Fetch and store user role
                role = get_user_role(email)
                st.session_state.role = role

                # Fetch client_id for logging
                from src.database.database_manager import DatabaseManager
                db = DatabaseManager()
                client = db.get_client(email=email)
                if client:
                    st.session_state.client_id = client['id']

                    # 31/08/2026 : distinction test/prod par compte — le
                    # mode n'était jusqu'ici JAMAIS lu depuis le compte, il
                    # restait figé sur "TEST" pour tout le monde (voir
                    # initialize_session() dans client_dashboard_main_new.py).
                    # On applique désormais le mode réellement stocké sur CE
                    # compte (colonne clients.account_mode, 'test' par défaut
                    # tant qu'il n'a pas été explicitement basculé en 'prod').
                    st.session_state.env_mode = (client.get('account_mode') or 'test').upper()

                    # Log Login Activity
                    # Audit du 26/08/2026 (suite) : ActivityLogger.log() ne
                    # possède pas de paramètre ip_address (voir sa
                    # signature dans src/utils/activity_logger.py) — cet
                    # appel levait un TypeError non rattrapé à CHAQUE
                    # connexion via le formulaire mot de passe, faisant
                    # planter l'application juste après une connexion
                    # valide. Cela ne s'était jamais vu jusqu'ici car ce
                    # chemin de code n'était atteint ni par l'auto-connexion
                    # après inscription, ni par la reconnexion automatique
                    # via token d'URL (F5) — seul un vrai clic/Entrée sur
                    # "Se connecter" avec compte déjà existant l'atteint.
                    from src.utils.activity_logger import ActivityLogger
                    ActivityLogger.log(
                        client_id=client['id'],
                        action='login',
                        details={'role': role},
                    )

                    try:
                        from src.logging.audit import log_user_login
                        log_user_login(user_email=email, success=True, role=role)
                    except Exception:
                        pass  # audit logging must never block login
                else:
                    # Pas de ligne `clients` retrouvée (edge case) : on
                    # retombe sur TEST par défaut plutôt que de laisser
                    # env_mode non défini.
                    st.session_state.env_mode = "TEST"

                # —— Check onboarding status ————————————————
                try:
                    from src.onboarding.onboarding_manager import OnboardingManager
                    mgr = OnboardingManager(email)
                    st.session_state.onboarding_complete = mgr.is_onboarding_complete(email)
                except Exception:
                    st.session_state.onboarding_complete = True  # fail-safe: don't block login
                # ————————————————————————————————————

                st.success(f"✅ Connexion réussie ! (Rôle: {role})")
                st.rerun()
            else:
                st.error("❌ Mot de passe incorrect")
    
    # NOUVEAU: Lien "Mot de passe oublié ?"
    st.markdown("---")
    
    if st.checkbox("🔑 Mot de passe oublié ?"):
        _render_password_reset_form()


def _render_password_reset_form():
    """Render the password reset form."""
    st.markdown("### Réinitialisation du mot de passe")
    
    with st.form("reset_password_form"):
        reset_email = st.text_input("Votre email", placeholder="votre@email.com")
        new_password = st.text_input("Nouveau mot de passe", type="password", placeholder="Min. 6 caractères")
        confirm_password = st.text_input("Confirmer le mot de passe", type="password", placeholder="Retapez votre mot de passe")
        reset_submitted = st.form_submit_button("Réinitialiser le mot de passe", width='stretch')
        
        if reset_submitted:
            # Validation
            if not reset_email or not new_password or not confirm_password:
                st.error("⚠️ Tous les champs sont obligatoires")
            elif new_password != confirm_password:
                st.error("⚠️ Les mots de passe ne correspondent pas")
            elif len(new_password) < 6:
                st.error("⚠️ Le mot de passe doit contenir au moins 6 caractères")
            else:
                # Audit du 26/08/2026 (suite) : même correctif que la
                # connexion — l'existence du compte se vérifie avec
                # has_password(), pas avec get_credentials() (qui ne
                # reflète que la présence d'une boutique connectée). Avec
                # l'ancien check, un client inscrit sans boutique ne
                # pouvait jamais réinitialiser son mot de passe.
                from src.auth.password_manager import has_password, set_client_password

                if has_password(reset_email):
                    # Réinitialiser le mot de passe
                    success = set_client_password(reset_email, new_password)
                    
                    if success:
                        st.success("✅ Mot de passe réinitialisé avec succès !")
                        st.info("Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")
                    else:
                        st.error("❌ Erreur lors de la réinitialisation")
                else:
                    st.error("❌ Email non trouvé. Vérifiez votre adresse email.")
    
    st.info("💡 En production, un email de vérification serait envoyé. Pour cette version, le mot de passe est directement réinitialisé.")


def _render_registration_form():
    """Render minimal registration form — email + password only.
    Store connection, IBAN, and API keys are collected in the onboarding wizard.
    """
    st.markdown("### ✨ Créer votre compte")
    st.caption("En 30 secondes — le reste se configure dans l'assistant après connexion.")

    with st.form("registration_form"):
        reg_email = st.text_input(
            "📧 Email professionnel",
            placeholder="contact@maboutique.com",
        )
        reg_password = st.text_input(
            "🔒 Mot de passe",
            type="password",
            placeholder="Min. 6 caractères",
        )
        reg_password_confirm = st.text_input(
            "🔒 Confirmer le mot de passe",
            type="password",
            placeholder="Retapez votre mot de passe",
        )

        accept_terms = st.checkbox(
            "J'accepte les [conditions d'utilisation](https://refundly.fr/cgu) et la politique de confidentialité"
        )

        register_submitted = st.form_submit_button(
            "🚀 Créer mon compte gratuitement",
            use_container_width=True,
            type="primary",
        )

    if register_submitted:
        # Basic validation
        if not reg_email or not reg_password or not reg_password_confirm:
            st.error("⚠️ Tous les champs sont obligatoires.")
            return
        if reg_password != reg_password_confirm:
            st.error("⚠️ Les mots de passe ne correspondent pas.")
            return
        if len(reg_password) < 6:
            st.error("⚠️ Le mot de passe doit comporter au moins 6 caractères.")
            return
        if not accept_terms:
            st.warning("⚠️ Veuillez accepter les conditions d'utilisation.")
            return

        # Register with minimal info
        _process_registration(
            reg_email, reg_password, reg_password_confirm,
            store_name="", store_url="",
            platform="", api_key="", api_secret="",
            reg_iban="", reg_account_holder="", reg_bic="",
            accept_terms=accept_terms,
        )


def _render_platform_fields(platform):
    """
    Render platform-specific API fields.
    
    Args:
        platform (str): The e-commerce platform name.
        
    Returns:
        tuple: (api_key, api_secret) values.
    """
    if platform == "Shopify":
        with st.expander("❓ Où trouver mes identifiants Shopify ?"):
            st.markdown("""
            1. Connectez-vous à votre interface **Shopify Admin**.
            2. Allez dans **Paramètres** > **Applis et canaux de vente**.
            3. Cliquez sur **Développer des applications**.
            4. Créez une application et accordez les accès scope `read_orders` et `read_shipping`.
            5. Installez l'app pour obtenir votre **Access Token**.
            """)
        api_key = st.text_input("Shop URL", placeholder="maboutique.myshopify.com")
        api_secret = st.text_input("Access Token", type="password")
    elif platform == "WooCommerce":
        with st.expander("❓ Où trouver mes identifiants WooCommerce ?"):
            st.markdown("""
            1. Allez dans **WooCommerce** > **Réglages** > **Avancé**.
            2. Cliquez sur **REST API**.
            3. Cliquez sur **Ajouter une clé**.
            4. Donnez des droits de **Lecture/Écriture**.
            5. Copiez la **Consumer Key** et le **Consumer Secret**.
            """)
        api_key = st.text_input("Consumer Key", placeholder="ck_xxxxx")
        api_secret = st.text_input("Consumer Secret", type="password", placeholder="cs_xxxxx")
    elif platform == "PrestaShop":
        with st.expander("❓ Où trouver mes identifiants PrestaShop ?"):
            st.markdown("""
            1. Allez dans **Paramètres avancés** > **Webservice**.
            2. Cliquez sur **Ajouter une clé de webservice**.
            3. Cliquez sur **Générer** pour créer votre clé.
            4. Cochez les permissions pour `orders` et `order_details` (GET/POST).
            5. Enregistrez et copiez la clé.
            """)
        api_key = st.text_input("Webservice Key", placeholder="Votre clé PrestaShop")
        api_secret = st.text_input("Password (si requis)", type="password", placeholder="Laisser vide si pas de mot de passe")
    elif platform == "Magento":
        with st.expander("❓ Où trouver mes identifiants Magento ?"):
            st.markdown("""
            1. Allez dans **System** > **Extensions** > **Integrations**.
            2. Cliquez sur **Add New Integration**.
            3. Donnez accès aux ressources "Sales" et "Orders".
            4. Cliquez sur **Activate** pour obtenir vos tokens.
            5. Copiez l'**Access Token**.
            """)
        api_key = st.text_input("Access Token", type="password", placeholder="Votre token Magento")
        api_secret = st.text_input("Store Code", placeholder="default")
    elif platform == "Wix":
        with st.expander("❓ Où trouver mes identifiants Wix ?"):
            st.markdown("""
            1. Allez sur le **Wix Dev Center**.
            2. Créez une application pour votre site.
            3. Dans **Permissions**, ajoutez l'accès aux commandes (Orders).
            4. Copiez l'**API Key** et l'**App ID**.
            """)
        api_key = st.text_input("API Key", type="password")
        api_secret = st.text_input("Site ID / App ID")
    else:
        api_key = st.text_input("API Key / Client ID", placeholder="Votre clé API")
        api_secret = st.text_input("API Secret / Client Secret", type="password", placeholder="Votre secret API")
    
    return api_key, api_secret


def register_client(reg_email, reg_password, reg_password_confirm, store_name, store_url,
                    platform, api_key, api_secret, reg_iban, reg_account_holder, reg_bic, accept_terms,
                    credentials_manager: CredentialsManager = None,
                    password_setter=None,
                    onboarding_manager: OnboardingManager = None,
                    email_sender=None):
    """Register a new client (testable helper).

    Returns:
        dict: { 'success': bool, 'errors': list }
    """
    errors = []

    # Basic validations
    if not reg_email or not reg_password or not reg_password_confirm:
        errors.append("⚠️ Tous les champs sont obligatoires")

    if reg_password != reg_password_confirm:
        errors.append("⚠️ Les mots de passe ne correspondent pas")

    if len(reg_password) < 6:
        errors.append("⚠️ Le mot de passe doit contenir au moins 6 caractères")

    if not accept_terms:
        errors.append("⚠️ Vous devez accepter les conditions d'utilisation")

    # Managers defaults
    manager = credentials_manager or CredentialsManager()

    # Audit du 26/08/2026 (suite) : SÉCURITÉ — cette vérification de
    # doublon s'appuyait sur manager.get_credentials(reg_email), c'est-à-
    # dire sur la présence d'une boutique connectée, pas sur l'existence
    # réelle du compte. Depuis que l'inscription simplifiée ne connecte
    # plus de boutique par défaut (voir plus bas), un compte existant sans
    # boutique n'était PLUS détecté comme doublon : n'importe qui
    # connaissant l'email d'un client pouvait « se réinscrire » avec ce
    # même email et écraser silencieusement son mot de passe (prise de
    # contrôle de compte sans connaître l'ancien mot de passe). La bonne
    # vérification d'existence est has_password(), indépendante de toute
    # boutique — cohérent avec la connexion et la réinitialisation.
    from src.auth.password_manager import has_password
    if has_password(reg_email):
        errors.append("⚠️ Cet email est déjà utilisé. Utilisez l'onglet 'Connexion'.")

    if errors:
        return { 'success': False, 'errors': errors }

    # Audit du 26/08/2026 : _render_registration_form() est le formulaire
    # d'inscription simplifié (email + mot de passe uniquement — la
    # connexion boutique se fait après coup, dans l'écran d'accueil /
    # Réglages) et appelle register_client() avec platform="" et tous les
    # champs boutique vides. Avant ce correctif, le code ci-dessous
    # appelait store_credentials() SANS CONDITION, même avec des champs
    # vides : ça créait pour CHAQUE inscription une fausse ligne boutique
    # ("** Store**" / "** Magasin **" selon les cas) dans Réglages, jamais
    # réellement connectée, mais affichée comme si elle l'était. On ne
    # crée désormais une ligne boutique que si une plateforme a
    # effectivement été renseignée.
    success = True
    if platform:
        # Build credentials dict
        credentials = {
            'shop_url': store_url if platform == "Shopify" else api_key,
            'access_token': api_secret,
            'store_name': store_name,
        }

        if platform == "WooCommerce":
            credentials['consumer_key'] = api_key
            credentials['consumer_secret'] = api_secret

        success = manager.store_credentials(
            client_id=reg_email,
            platform=platform.lower(),
            credentials=credentials
        )

    # Store bank info ONLY if provided
    if reg_iban:
        try:
            from src.payments.manual_payment_manager import add_bank_info
            add_bank_info(
                client_email=reg_email,
                iban=reg_iban.replace(" ", "").upper(),
                bic=reg_bic.upper() if reg_bic else None,
                account_holder_name=reg_account_holder if reg_account_holder else reg_email.split('@')[0],
                bank_name="Banque Source"
            )
        except Exception:
            # Non-fatal
            pass

    if not success:
        return { 'success': False, 'errors': ["❌ Erreur lors de la création du compte"] }

    # Créer la ligne canonique dans la table `clients` (audit du 26/08/2026 :
    # cette étape manquait entièrement — l'inscription créait des identifiants
    # de connexion (CredentialsManager, table séparée keyée par email) mais
    # AUCUNE ligne dans la table `clients`. Résultat : après inscription,
    # db.get_client(email=...) retournait toujours None, donc client_id ne
    # se peuplait jamais en session, cassant silencieusement "Analyses"
    # ("aucune fiche client associée à ce compte") et "Gestion des Litiges"
    # ("Client introuvable") pour TOUT nouveau compte, alors même que
    # l'assistant d'onboarding affichait "Votre compte est configuré !".
    try:
        from src.database.database_manager import DatabaseManager
        _db = DatabaseManager()
        _db.create_client(email=reg_email, company_name=store_name)
    except Exception as e:
        # Non-fatal pour ne pas bloquer l'inscription, mais on log pour
        # pouvoir diagnostiquer si Analyses/Gestion restent cassés ensuite.
        logger.warning(f"create_client a échoué pendant l'inscription de {reg_email}: {e}")

    # Set password
    pwd_setter = password_setter or (lambda email, pwd: __import__('auth.password_manager', fromlist=['set_client_password']).set_client_password(email, pwd))
    pwd_success = pwd_setter(reg_email, reg_password)

    if not pwd_success:
        return { 'success': False, 'errors': ["❌ Erreur lors de la création du mot de passe"] }

    # Send welcome email (best effort)
    if email_sender:
        try:
            email_sender.send_welcome_email(recipient_email=reg_email, store_name=store_name)
        except Exception:
            pass

    # Initialize onboarding
    onboard_mgr = onboarding_manager or OnboardingManager()
    try:
        onboard_mgr.initialize_onboarding(reg_email)
    except Exception:
        # best effort
        pass

    return { 'success': True, 'errors': [] }


def _process_registration(reg_email, reg_password, reg_password_confirm, store_name, store_url,
                          platform, api_key, api_secret, reg_iban, reg_account_holder, reg_bic, accept_terms):
    """Process the registration form submission (UI wrapper)."""
    result = register_client(
        reg_email, reg_password, reg_password_confirm, store_name, store_url,
        platform, api_key, api_secret, reg_iban, reg_account_holder, reg_bic, accept_terms
    )

    if not result['success']:
        for error in result['errors']:
            st.error(error)
        return

    # Success path: configure session and redirect to client dashboard
    st.success("🎉 Compte créé avec succès !")
    st.info("👉 Plus que 2 étapes pour finaliser votre espace : IBAN et bienvenue !")
    st.balloons()

    try:
        from src.logging.audit import log_user_created
        log_user_created(user_email=reg_email, platform=platform)
    except Exception:
        pass  # audit logging must never block registration

    # Auto-login
    # Audit du 26/08/2026 (suite) : voir le commentaire équivalent dans
    # _render_login_form() — repart d'une URL propre pour ce nouveau compte.
    st.query_params.clear()
    st.session_state.authenticated = True
    st.session_state.client_email = reg_email
    st.session_state.role = 'client'  # Default role for new users
    st.session_state.onboarding_complete = False  # Ensure new users go to wizard

    # Fetch client_id for analytics and logging (mirrors login flow)
    try:
        from src.database.database_manager import DatabaseManager
        db = DatabaseManager()
        client = db.get_client(email=reg_email)
        if client:
            st.session_state.client_id = client['id']
            # 31/08/2026 : un nouveau compte est 'test' par défaut
            # (colonne clients.account_mode, DEFAULT 'test') tant qu'il n'a
            # pas été explicitement basculé en 'prod' — voir _render_login_form.
            st.session_state.env_mode = (client.get('account_mode') or 'test').upper()
    except Exception:
        pass  # Non-fatal — analytics will gracefully show "Session invalide" if missing

    # Set flags to open portal and redirect to dashboard inline
    st.session_state.show_portal = True
    st.session_state.redirect_to_dashboard = True

    # Rerun to apply the redirect
    st.rerun()
