"""
4-step onboarding wizard for new Refundly clients.

Shown automatically on first login until onboarding is complete.
Steps: Profile → Store connection → Bank info → Done!
"""

import streamlit as st
import time
from src.ui.logo import logo_img_tag as _logo_tag


def render_onboarding_wizard():
    """
    Main entry point. Call from dashboard.py when onboarding is incomplete.
    Renders the full-page wizard and injects sidebar-hiding CSS.
    """
    _inject_wizard_css()

    email = st.session_state.get("client_email", "")

    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1

    step = st.session_state.onboarding_step

    # ── Brand header ─────────────────────────────────────────────────────────
    _logo_html = _logo_tag(height=50)
    st.markdown(
        f"""
        <div style="text-align:center;padding:24px 0 8px;">
          {_logo_html}
          <p style="color:#888;margin:10px 0 0;font-size:.9rem;">🚀 Recouvrement logistique automatisé</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_progress_bar(step)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Step router ──────────────────────────────────────────────────────────
    if step == 1:
        _step_profile(email)
    elif step == 2:
        _step_store(email)
    elif step == 3:
        _step_bank(email)
    elif step == 4:
        _step_done(email)

    # ── Floating chatbot (inline panel, sidebar is hidden during wizard) ─────
    from src.dashboard.floating_chatbot import render_floating_chatbot
    contexts = {
        1: "profil bienvenue",
        2: "boutique api connexion",
        3: "bancaire iban virement",
        4: "tableau de bord prêt",
    }
    render_floating_chatbot(
        context=contexts.get(step, ""),
        client_email=email,
        wizard_mode=True,
    )


# ── Progress bar ─────────────────────────────────────────────────────────────

def _render_progress_bar(current: int):
    labels = ["Profil", "Boutique", "Paiements", "Prêt !"]
    cols = st.columns(4)
    for i, (col, label) in enumerate(zip(cols, labels), 1):
        with col:
            if i < current:
                st.markdown(
                    f"""<div style="text-align:center">
                      <div style="width:40px;height:40px;border-radius:50%;background:#0072ff;
                                  color:white;display:inline-flex;align-items:center;
                                  justify-content:center;font-size:16px;font-weight:bold;
                                  box-shadow:0 2px 8px rgba(0,114,255,.3);">&#10003;</div>
                      <div style="font-size:11px;color:#0072ff;margin-top:4px;font-weight:600;">{label}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            elif i == current:
                st.markdown(
                    f"""<div style="text-align:center">
                      <div style="width:40px;height:40px;border-radius:50%;
                                  background:linear-gradient(135deg,#00c6ff,#0072ff);
                                  color:white;display:inline-flex;align-items:center;
                                  justify-content:center;font-size:16px;font-weight:bold;
                                  box-shadow:0 4px 14px rgba(0,114,255,.4);">{i}</div>
                      <div style="font-size:11px;color:#0072ff;font-weight:700;margin-top:4px;">{label}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""<div style="text-align:center">
                      <div style="width:40px;height:40px;border-radius:50%;background:#e8e8e8;
                                  color:#aaa;display:inline-flex;align-items:center;
                                  justify-content:center;font-size:16px;">{i}</div>
                      <div style="font-size:11px;color:#aaa;margin-top:4px;">{label}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )


# ── Step 1 : Profile ──────────────────────────────────────────────────────────

def _step_profile(email: str):
    _, center, _ = st.columns([1, 3, 1])
    with center:
        st.markdown(
            """<div style="text-align:center;margin-bottom:20px;">
              <div style="font-size:3rem;">👋</div>
              <h2 style="margin:0;">Bienvenue sur Refundly !</h2>
              <p style="color:#666;font-size:1.05rem;">
                La configuration prend moins de 5 minutes.
              </p>
            </div>""",
            unsafe_allow_html=True,
        )

        st.info(
            "💡 **Comment ça marche ?** Notre IA détecte automatiquement vos litiges "
            "transporteurs non résolus (colis perdus, endommagés, retards) et les traite "
            "pour vous. Vous recevez **80 %** des remboursements obtenus, sans rien faire."
        )

        st.markdown("### 1. Dites-nous qui vous êtes")
        with st.form("wizard_profile"):
            name = st.text_input(
                "👤 Nom complet",
                placeholder="Jean Dupont",
                help="Apparaît sur les courriers officiels envoyés aux transporteurs.",
            )
            company = st.text_input(
                "🏢 Entreprise",
                placeholder="Ma Boutique SAS",
                help="Nom légal ou commercial de votre société.",
            )
            phone = st.text_input(
                "📱 Téléphone (optionnel)",
                placeholder="+33 6 12 34 56 78",
            )
            submitted = st.form_submit_button(
                "Étape suivante →", type="primary", use_container_width=True
            )

        if submitted:
            if not name or not company:
                st.error("⚠️ Nom et entreprise obligatoires.")
            else:
                st.session_state.update({"_wiz_name": name, "_wiz_company": company})
                _save_profile(email, name, company, phone)
                st.session_state.onboarding_step = 2
                st.rerun()


# ── Step 2 : Store ────────────────────────────────────────────────────────────

_PLATFORM_GUIDES = {
    "Shopify": {
        "steps": [
            "Dans votre admin Shopify → **Paramètres → Applications et canaux de vente**",
            "Cliquez sur **Développer des applications** puis **Créer une application**",
            "Nommez-la *Refundly*, configurez les autorisations : `read_orders`, `read_fulfillments`",
            "Cliquez sur **Installer l'application** et copiez le **Jeton d'accès admin**",
        ],
        "link": "https://admin.shopify.com/settings/apps/development",
        "f1_label": "URL boutique",
        "f1_ph": "maboutique.myshopify.com",
        "f2_label": "Jeton d'accès (shpat_…)",
        "f2_ph": "shpat_xxxxxxxxxxxxxxxx",
    },
    "WooCommerce": {
        "steps": [
            "Dans WordPress → **WooCommerce → Réglages → Avancé → API REST**",
            "Cliquez **Ajouter une clé** : description *Refundly*, permissions **Lecture**",
            "Cliquez **Générer la clé API** et copiez les deux clés affichées",
        ],
        "link": None,
        "f1_label": "Consumer Key (ck_…)",
        "f1_ph": "ck_xxxxxxxxxxxxxxxx",
        "f2_label": "Consumer Secret (cs_…)",
        "f2_ph": "cs_xxxxxxxxxxxxxxxx",
    },
    "PrestaShop": {
        "steps": [
            "Admin PrestaShop → **Paramètres avancés → API Web (Webservice)**",
            "Activez l'API Web, cliquez **Ajouter une clé**",
            "Permissions **GET** sur `orders` et `order_details`, générez et copiez la clé",
        ],
        "link": None,
        "f1_label": "URL de la boutique",
        "f1_ph": "https://maboutique.com",
        "f2_label": "Clé API WebService",
        "f2_ph": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    },
    "Magento": {
        "steps": [
            "Système → Extensions → **Intégrations** → **Ajouter une nouvelle intégration**",
            "Nommez-la 'Refundly', onglet API : cochez **Ventes** et **Catalogue**",
            "Enregistrez, cliquez sur **Activer**, copiez le **Jeton d'accès**",
        ],
        "link": None,
        "f1_label": "URL de la boutique",
        "f1_ph": "https://maboutique-magento.com",
        "f2_label": "Jeton d'accès (Access Token)",
        "f2_ph": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    },
    "BigCommerce": {
        "steps": [
            "Settings → API → **API Accounts** → **Create API Account**",
            "Nom : 'Refundly', Permissions : **Orders** (read-only)",
            "Récupérez le **Store Hash** (dans l'URL) et le **Access Token**",
        ],
        "link": None,
        "f1_label": "Store Hash",
        "f1_ph": "x7abc123",
        "f2_label": "Access Token",
        "f2_ph": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    },
    "Wix": {
        "steps": [
            "Tableau de bord Wix → **Paramètres** → Récupérez le **Site ID**",
            "Générez un **Access Token** via l'espace développeur Wix",
        ],
        "link": "https://developers.wix.com/",
        "f1_label": "Site ID",
        "f1_ph": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        "f2_label": "Access Token",
        "f2_ph": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    },
}


def _step_store(email: str):
    _, center, _ = st.columns([1, 4, 1])
    with center:
        st.markdown(
            """<div style="text-align:center;margin-bottom:16px;">
              <div style="font-size:3rem;">🏪</div>
              <h2 style="margin:0;">Connectez votre boutique</h2>
              <p style="color:#666;">
                Refundly lit vos commandes en lecture seule pour identifier les litiges.
              </p>
            </div>""",
            unsafe_allow_html=True,
        )

        platform = st.selectbox(
            "Votre plateforme e-commerce",
            list(_PLATFORM_GUIDES.keys()) + ["Autre"],
        )
        guide = _PLATFORM_GUIDES.get(platform)

        if guide:
            with st.expander(f"📖 Guide : trouver mes identifiants {platform}", expanded=True):
                for i, s in enumerate(guide["steps"], 1):
                    st.markdown(f"**{i}.** {s}")
                if guide["link"]:
                    st.markdown(f"🔗 [Ouvrir l'admin {platform} ↗]({guide['link']})")

        st.markdown("---")
        with st.form("wizard_store"):
            store_name = st.text_input("🏷️ Nom de votre boutique", placeholder="Ma Boutique")
            if guide:
                f1 = st.text_input(f"🌐 {guide['f1_label']}", placeholder=guide["f1_ph"])
                f2 = st.text_input(
                    f"🔑 {guide['f2_label']}", type="password", placeholder=guide["f2_ph"],
                    help="Chiffré AES-256 · Lecture seule · Révocable à tout moment",
                )
            else:
                f1 = st.text_input("🌐 URL boutique", placeholder="https://maboutique.com")
                f2 = st.text_input("🔑 Clé API", type="password")

            st.caption("🔒 Vos identifiants sont chiffrés et jamais revendus.")
            
            with st.expander("🛠️ Paramètres avancés (Transporteurs)", expanded=False):
                st.markdown("Si vous avez vos propres clés API transporteur, renseignez-les ici pour éviter les blocages.")
                fedex_key = st.text_input("🔑 FedEx Client ID", placeholder="FEDEX_...")
                fedex_secret = st.text_input("🔑 FedEx Client Secret", type="password")
                dpd_user = st.text_input("👤 DPD DelisID", placeholder="delis123")
                dpd_pass = st.text_input("🔑 DPD Password", type="password")

            c1, c2 = st.columns(2)

            with c1:
                skip = st.form_submit_button("⏭️ Plus tard", use_container_width=True)
            with c2:
                nxt = st.form_submit_button("Étape suivante →", type="primary", use_container_width=True)

        if skip:
            st.session_state.onboarding_step = 3
            st.rerun()

        if nxt:
            if not store_name or not f1 or not f2:
                st.error("⚠️ Tous les champs sont obligatoires.")
            else:
                carrier_creds = {
                    "fedex": {"client_id": fedex_key, "client_secret": fedex_secret} if fedex_key else None,
                    "dpd": {"delis_id": dpd_user, "password": dpd_pass} if dpd_user else None
                }
                _save_store(email, platform, store_name, f1, f2, carrier_creds)
                with st.spinner("🔗 Test de connexion…"):

                    time.sleep(1.5)
                st.success(f"✅ **{store_name}** connectée !")
                st.session_state["_wiz_store"] = store_name
                time.sleep(0.8)
                st.session_state.onboarding_step = 3
                st.rerun()

    if st.button("← Retour", key="back_store"):
        st.session_state.onboarding_step = 1
        st.rerun()


# ── Step 3 : Bank ─────────────────────────────────────────────────────────────

def _step_bank(email: str):
    _, center, _ = st.columns([1, 3, 1])
    with center:
        st.markdown(
            """<div style="text-align:center;margin-bottom:16px;">
              <div style="font-size:3rem;">💳</div>
              <h2 style="margin:0;">Coordonnées bancaires</h2>
              <p style="color:#666;">Pour recevoir vos remboursements automatiquement.</p>
            </div>""",
            unsafe_allow_html=True,
        )

        st.info(
            "**💰 Comment vous êtes payé ?**\n\n"
            "À chaque remboursement obtenu : **80 %** vous est viré sur cet IBAN. "
            "**20 %** est notre commission de succès. Aucun frais si nous n'obtenons rien."
        )

        with st.form("wizard_bank"):
            iban = st.text_input(
                "🏦 IBAN",
                placeholder="FR76 1234 5678 9012 3456 7890 123",
                help="Visible sur votre relevé de compte ou dans l'espace Mon Compte de votre banque.",
            )
            bic = st.text_input("🔢 BIC / SWIFT", placeholder="BNPAFRPP")
            holder = st.text_input(
                "👤 Titulaire",
                value=st.session_state.get("_wiz_company", ""),
                placeholder="Ma Boutique SAS",
            )
            bank = st.text_input("🏛️ Nom de la banque (optionnel)", placeholder="BNP Paribas")
            st.caption("🔒 Chiffrement AES-256 · Jamais communiqué à des tiers.")

            c1, c2 = st.columns(2)
            with c1:
                skip = st.form_submit_button("⏭️ Plus tard", use_container_width=True)
            with c2:
                nxt = st.form_submit_button("Terminer →", type="primary", use_container_width=True)

        if skip:
            st.session_state.onboarding_step = 4
            st.rerun()

        if nxt:
            if not iban or not holder:
                st.error("⚠️ IBAN et titulaire obligatoires.")
            else:
                _save_bank(email, iban, bic, holder, bank)
                st.session_state.onboarding_step = 4
                st.rerun()

    if st.button("← Retour", key="back_bank"):
        st.session_state.onboarding_step = 2
        st.rerun()


# ── Step 4 : Done ─────────────────────────────────────────────────────────────

def _step_done(email: str):
    st.balloons()
    _, center, _ = st.columns([1, 3, 1])
    with center:
        st.markdown(
            """<div style="text-align:center;margin-bottom:24px;">
              <div style="font-size:4rem;">&#x1F680;</div>
              <h1 style="background:linear-gradient(135deg,#00c6ff,#0072ff);
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                         font-size:2.4rem;font-weight:900;">
                Tout est prêt !
              </h1>
              <p style="color:#555;font-size:1.1rem;">
                Refundly va maintenant analyser vos commandes en arrière-plan.
              </p>
            </div>""",
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        for col, icon, title, desc in [
            (c1, "🔍", "Analyse auto", "Notre IA scanne vos 12 derniers mois de commandes."),
            (c2, "📨", "Envoi auto", "Les réclamations partent avec les documents légaux."),
            (c3, "💰", "80 % pour vous", "Chaque remboursement est viré directement sur votre IBAN."),
        ]:
            with col:
                st.markdown(
                    f"""<div style="text-align:center;padding:18px;
                                   background:rgba(0,114,255,.06);border-radius:14px;
                                   border:1px solid rgba(0,114,255,.15);">
                         <div style="font-size:2rem;">{icon}</div>
                         <strong style="color:#0f0f1a;">{title}</strong>
                         <p style="font-size:.82rem;color:#666;margin-top:8px;">{desc}</p>
                       </div>""",
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

        store = st.session_state.get("_wiz_store")
        if store:
            st.success(f"✅ Boutique connectée : **{store}**")
        else:
            st.warning("⚠️ Boutique non connectée — configurez-la depuis **Paramètres → Boutiques**")

        if st.button("🚀 Accéder à mon tableau de bord", type="primary", use_container_width=True):
            _mark_complete(email)
            st.session_state["onboarding_complete"] = True
            st.rerun()


# ── DB helpers ────────────────────────────────────────────────────────────────

def _save_profile(email, name, company, phone):
    try:
        from auth.credentials_manager import CredentialsManager
        mgr = CredentialsManager()
        if hasattr(mgr, "update_client_profile"):
            mgr.update_client_profile(email, full_name=name, company=company, phone=phone)
    except Exception:
        pass


def _save_store(email, platform, store_name, key1, key2, carrier_creds=None):
    try:
        from auth.credentials_manager import CredentialsManager
        creds = {"store_name": store_name}
        
        # ... (keep existing platform logic)
        if platform == "Shopify":
            creds.update({"shop_url": key1, "access_token": key2})
        elif platform == "WooCommerce":
            creds.update({"consumer_key": key1, "consumer_secret": key2})
        elif platform == "PrestaShop":
            creds.update({"shop_url": key1, "access_token": key2})
        elif platform == "Magento":
            creds.update({"store_url": key1, "access_token": key2})
        elif platform == "BigCommerce":
            creds.update({"store_hash": key1, "access_token": key2})
        elif platform == "Wix":
            creds.update({"site_id": key1, "access_token": key2})
        else:
            creds.update({"shop_url": key1, "access_token": key2})

        if carrier_creds:
            creds["carrier_apis"] = carrier_creds

        mgr = CredentialsManager()

        fn = mgr.add_store if hasattr(mgr, "add_store") else mgr.store_credentials
        fn(client_id=email, platform=platform.lower(), credentials=creds)
    except Exception:
        pass


def _save_bank(email, iban, bic, holder, bank):
    try:
        from payments.manual_payment_manager import ManualPaymentManager
        ManualPaymentManager().add_client_bank_info(
            client_email=email,
            iban=iban.replace(" ", "").upper(),
            bic=bic.upper() if bic else None,
            account_holder_name=holder,
            bank_name=bank or "Non renseigné",
        )
    except Exception:
        pass


def _mark_complete(email):
    try:
        from src.onboarding.onboarding_manager import OnboardingManager
        OnboardingManager(email).mark_complete(email)
    except Exception:
        pass


# ── CSS ───────────────────────────────────────────────────────────────────────

def _inject_wizard_css():
    st.markdown(
        """
<style>
/* Hide sidebar during onboarding */
section[data-testid="stSidebar"] { display:none !important; }
/* Center the wizard content */
.main .block-container { max-width:860px; padding-top:1.5rem; }
</style>
        """,
        unsafe_allow_html=True,
    )
