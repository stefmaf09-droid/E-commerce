"""
src/dashboard/welcome_hub.py

Écran d'accueil affiché une seule fois, juste après la connexion — en
remplacement de l'ancien assistant d'inscription obligatoire à 3 étapes
(onboarding_functions.render_onboarding).

Audit du 26/08/2026 — pourquoi ce remplacement :

1. Bug bloquant (urgent) : l'ancien assistant bloquait TOUS les nouveaux
   clients dès l'étape 1 ("Connectez votre boutique"). Le bouton
   "Continuer" appelait OnboardingManager.mark_step_complete(), qui faisait
   un UPDATE SQL sur une ligne qui n'existait pas encore pour un nouveau
   client (aucun INSERT préalable nulle part dans le flux réel) — la mise
   à jour ne touchait donc 0 ligne, silencieusement, sans la moindre
   erreur visible. Résultat : l'assistant rechargeait et retombait
   systématiquement sur l'étape 1, en boucle infinie. Corrigé à la racine
   dans OnboardingManager (INSERT OR IGNORE avant chaque UPDATE), et cet
   écran s'assure en plus qu'une ligne existe dès son affichage.

2. Expérience client demandée : un tunnel à 3 étapes obligatoires
   (boutique -> IBAN -> écran de bienvenue avec pavé de texte) est plus
   lourd que nécessaire. Cet écran unique va à l'essentiel : un raccourci
   direct pour le cas le plus fréquent ("je veux juste déposer une preuve
   de livraison"), et une checklist compacte et facultative pour le reste
   (boutique / IBAN), modifiable à tout moment depuis Réglages. Rien n'est
   bloquant : un client peut accéder à son tableau de bord immédiatement.

Tous les boutons de cet écran sont des st.button() simples (jamais de
st.form / st.form_submit_button) : le bug de navigation initial de la
barre du haut ET celui de ce fichier ont tous les deux été tracés à des
composants rendus dans un contexte qui n'exécutait pas fiablement le
callback attendu — st.button() natif est le seul pattern vérifié fiable
dans cette application (voir client_dashboard_main_new.py::_render_top_navbar).
"""

import streamlit as st

from src.auth.credentials_manager import CredentialsManager
from src.payments.manual_payment_manager import ManualPaymentManager


def _get_setup_status(client_email: str):
    """État réel des prérequis (boutique / IBAN), lu en direct plutôt que
    via le suivi interne d'onboarding (qui peut être obsolète ou
    désynchronisé — voir needs_welcome_hub ci-dessous)."""
    stores = []
    try:
        # Audit du 26/08/2026 : on écarte les lignes "fantômes" (plateforme
        # vide) — un bug séparé dans l'inscription simplifiée créait une
        # fausse ligne boutique pour chaque nouveau client (voir le fix
        # dans auth_functions.py::register_client). On filtre ici par
        # sécurité, y compris pour les comptes déjà touchés par ce bug.
        stores = [s for s in CredentialsManager().get_all_stores(client_email) if s.get("platform")]
    except Exception:
        pass
    store_connected = len(stores) > 0

    bank_connected = False
    try:
        bank_info = ManualPaymentManager().get_client_bank_info(client_email)
        bank_connected = bool(bank_info and bank_info.get("iban"))
    except Exception:
        pass

    return store_connected, bank_connected, stores


def needs_welcome_hub(client_email: str) -> bool:
    """True si ce client a encore quelque chose à configurer (boutique ou
    IBAN) — utilisé par le point d'entrée pour décider d'afficher l'accueil.

    Audit du 26/08/2026 (suite) : le point d'entrée s'appuyait auparavant
    uniquement sur le flag permanent onboarding_status.onboarding_complete
    pour savoir s'il fallait afficher cet écran. Ce flag peut être obsolète
    (positionné à True par l'ancien système, avant même que cet écran
    n'existe — cas de plusieurs comptes existants) et rester alors bloqué à
    True indéfiniment, empêchant l'écran de s'afficher même si rien n'est
    réellement configuré. On calcule donc ici l'état réel, comme le fait
    déjà _get_setup_status() pour la checklist.
    """
    if not client_email:
        return False
    store_connected, bank_connected, _ = _get_setup_status(client_email)
    return not (store_connected and bank_connected)


def _go_to(tab_label: str, onboarding_manager, client_email: str):
    """Marque l'accueil comme vu (pour cette session ET de façon
    persistante dans l'URL) et bascule vers l'onglet demandé.

    Audit du 26/08/2026 (suite) : le point d'entrée (client_dashboard_
    main_new.py) tamponne systématiquement `token`/`page` dans l'URL pour
    TOUT utilisateur authentifié, dès le rendu suivant l'inscription ou la
    connexion (protection F5, sans rapport avec un vrai choix de
    navigation). On ne peut donc pas se fier à la simple présence de
    `page` dans l'URL pour savoir si le client a réellement quitté cet
    écran. `hub_seen` est un marqueur dédié, positionné uniquement ici,
    qui survit à un F5 (contrairement au session_state) sans être posé
    par erreur par ce mécanisme de bookkeeping.
    """
    onboarding_manager.mark_complete(client_email)
    st.session_state["_welcome_hub_dismissed"] = True
    st.session_state.active_tab = tab_label
    st.query_params["page"] = tab_label
    st.query_params["hub_seen"] = "1"
    st.rerun()


def render_welcome_hub(client_email: str, onboarding_manager):
    """Écran d'accueil unique, affiché juste après la connexion."""

    # Garantit qu'une ligne onboarding_status existe pour ce client avant
    # toute mise à jour ultérieure (voir l'audit en tête de fichier).
    try:
        onboarding_manager.initialize_onboarding(client_email)
    except Exception:
        pass

    store_connected, bank_connected, stores = _get_setup_status(client_email)

    first_name = client_email.split("@")[0].replace(".", " ").replace("_", " ").title() or "!"

    st.markdown(f"## 👋 Bonjour {first_name} !")
    st.caption("Un seul écran pour démarrer — vous pourrez toujours revenir sur ces réglages plus tard.")
    st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

    # ── Raccourci principal : déposer une preuve, sans rien configurer ────
    with st.container(border=True):
        col1, col2 = st.columns([3, 1], vertical_alignment="center")
        with col1:
            st.markdown("#### 📸 Juste une preuve de livraison à déposer ?")
            st.caption("Aucune configuration nécessaire — déposez votre document, on s'occupe du reste.")
        with col2:
            if st.button("Déposer maintenant →", type="primary", use_container_width=True, key="hub_upload"):
                _go_to("Dépôt Preuves", onboarding_manager, client_email)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown("##### Pour profiter de tout Refundly &nbsp;·&nbsp; <span style='color:#6b7280;font-weight:400;font-size:0.85rem;'>facultatif, modifiable à tout moment depuis Réglages</span>", unsafe_allow_html=True)

    # ── Checklist compacte (2 cases, facultatives) ─────────────────────────
    c1, c2 = st.columns(2)

    with c1:
        with st.container(border=True):
            if store_connected:
                st.markdown("✅ **Boutique connectée**")
                st.caption(stores[0].get("store_name") or "Détection automatique active.")
            else:
                st.markdown("⚠️ **Boutique non connectée**")
                st.caption("Pour la détection automatique des litiges.")
                with st.expander("Connecter une boutique"):
                    _render_quick_store_form(client_email)

    with c2:
        with st.container(border=True):
            if bank_connected:
                st.markdown("✅ **Coordonnées bancaires**")
                st.caption("Vos remboursements sont configurés.")
            else:
                st.markdown("⚠️ **Coordonnées bancaires**")
                st.caption("Pour recevoir vos remboursements.")
                with st.expander("Ajouter mon IBAN"):
                    _render_quick_bank_form(client_email)

    st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
    if st.button("🚀 Accéder à mon tableau de bord", type="primary", use_container_width=True, key="hub_dashboard"):
        _go_to("Dashboard", onboarding_manager, client_email)


def _render_quick_store_form(client_email: str):
    platform = st.selectbox(
        "Plateforme",
        ["Shopify", "WooCommerce", "PrestaShop", "Magento", "BigCommerce", "Wix"],
        key="hub_platform",
    )
    store_name = st.text_input("Nom de la boutique", placeholder="Ma Boutique", key="hub_store_name")
    store_url = st.text_input("URL de la boutique", placeholder="https://maboutique.com", key="hub_store_url")
    api_key = st.text_input(
        "Shop URL" if platform == "Shopify" else "Clé API",
        placeholder="maboutique.myshopify.com" if platform == "Shopify" else "",
        key="hub_api_key",
    )
    api_secret = st.text_input("Jeton d'accès / Secret", type="password", key="hub_api_secret")

    if st.button("💾 Enregistrer la boutique", key="hub_save_store", use_container_width=True):
        if not all([store_name, store_url, api_key, api_secret]):
            st.error("Merci de remplir tous les champs.")
        else:
            creds = {
                "api_key": api_key,
                "api_secret": api_secret,
                "shop_url": api_key if platform == "Shopify" else store_url,
                "store_url": store_url,
                "store_name": store_name,
            }
            ok = CredentialsManager().store_credentials(
                client_id=client_email,
                platform=platform.lower(),
                credentials=creds,
                store_name=store_name,
            )
            if ok:
                st.success("✅ Boutique connectée !")
                st.rerun()
            else:
                st.error("❌ Une erreur est survenue, réessayez.")


def _render_quick_bank_form(client_email: str):
    iban = st.text_input("IBAN", placeholder="FR76...", key="hub_iban")
    if st.button("💾 Enregistrer l'IBAN", key="hub_save_bank", use_container_width=True):
        if not iban:
            st.error("Merci de renseigner votre IBAN.")
        else:
            ManualPaymentManager().add_client_bank_info(client_email, iban.replace(" ", "").upper())
            st.success("✅ IBAN enregistré !")
            st.rerun()
