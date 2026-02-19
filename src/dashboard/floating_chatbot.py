"""
Floating chatbot component for Refundly.

Uses JavaScript (via streamlit.components.v1.html) to inject a truly fixed
🤖 button at bottom-right. The chat panel opens in the Streamlit sidebar,
which is naturally fixed-position.

For the onboarding wizard (sidebar hidden), the chat renders as an inline
expandable panel at the bottom of each step.
"""

import streamlit as st
import streamlit.components.v1 as components
import time


# ── Public API ────────────────────────────────────────────────────────────────

def render_floating_chatbot(context: str = "", client_email: str = "", wizard_mode: bool = False):
    """
    Render the floating 🤖 chatbot.

    In wizard_mode (sidebar hidden): inline expandable panel at bottom.
    In dashboard mode: sidebar-based chat panel.

    Args:
        context      : Description of current page/step for contextual welcome.
        client_email : Logged-in client email.
        wizard_mode  : True during onboarding wizard (sidebar is hidden).
    """
    _ensure_state(context)

    if wizard_mode:
        _render_wizard_inline_chat(context)
    else:
        _render_sidebar_chat(context)
        _inject_floating_js_button()


def render_proactive_suggestions(client_email: str):
    """Show proactive action proposals for an existing client (in sidebar)."""
    try:
        from src.ai.proactive_agent import analyze_client_situation
        situation = analyze_client_situation(client_email)
        proposals = [
            p for p in situation.get("proposals", [])
            if not st.session_state.get(f"dismissed_{p['id']}")
        ]
    except Exception:
        proposals = []

    if not proposals:
        return

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔔 Actions recommandées")
        for p in proposals[:3]:
            urgency = "🔴" if p.get("urgent") else "🟡"
            with st.expander(f"{urgency} {p['title']}"):
                st.markdown(p["description"])
                c1, c2 = st.columns(2)
                with c1:
                    if st.button(f"✅ {p['cta']}", key=f"do_{p['id']}", type="primary", use_container_width=True):
                        with st.spinner("Exécution…"):
                            from src.ai.proactive_agent import execute_action
                            result = execute_action(p["action"], p.get("params", {}), client_email)
                        if result.get("success"):
                            st.success(result["message"])
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(result.get("error", "Erreur inconnue"))
                with c2:
                    if st.button("⏭️", key=f"skip_{p['id']}", use_container_width=True):
                        st.session_state[f"dismissed_{p['id']}"] = True
                        st.rerun()


# ── Sidebar chat (dashboard mode, truly fixed) ────────────────────────────────

def _render_sidebar_chat(context: str):
    with st.sidebar:
        st.markdown(
            """
<div style="background:linear-gradient(135deg,#667eea,#764ba2);border-radius:14px;
            padding:14px 16px;margin-bottom:12px;color:white;">
  <div style="font-size:1.1rem;font-weight:700;">🤖 Assistant Refundly</div>
  <div style="font-size:.78rem;opacity:.85;">● En ligne · Toujours disponible</div>
</div>
            """,
            unsafe_allow_html=True,
        )

        # Display messages
        for msg in st.session_state.bot_messages[-6:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Quick questions (first open only)
        if len(st.session_state.bot_messages) <= 1:
            st.markdown("**Questions fréquentes :**")
            for q in _quick_questions(context):
                if st.button(q, key=f"_sq_{hash(q)}", use_container_width=True):
                    _handle_message(q, context)
                    st.rerun()

        # Chat input
        if user_msg := st.chat_input("Votre question…", key="_bot_sidebar_input"):
            _handle_message(user_msg, context)
            st.rerun()


# ── Wizard inline chat (wizard mode, expandable at bottom) ────────────────────

def _render_wizard_inline_chat(context: str):
    st.markdown("---")
    with st.expander("🤖 Besoin d'aide ? Posez votre question à l'assistant", expanded=False):
        st.markdown(
            f"""<div style="background:linear-gradient(135deg,#667eea,#764ba2);border-radius:10px;
                           padding:12px 16px;color:white;font-weight:600;margin-bottom:12px;">
                 🤖 Assistant Refundly · <span style="font-size:.8rem;font-weight:400;">
                 {_welcome_for_context(context)}</span></div>""",
            unsafe_allow_html=True,
        )

        # Messages
        for msg in st.session_state.bot_messages[-4:]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Quick questions
        if len(st.session_state.bot_messages) <= 1:
            for q in _quick_questions(context):
                if st.button(q, key=f"_wq_{hash(q)}", use_container_width=True):
                    _handle_message(q, context)
                    st.rerun()

        # Input
        if user_msg := st.chat_input("Votre question…", key="_bot_wizard_input"):
            _handle_message(user_msg, context)
            st.rerun()


# ── Truly floating JS button (dashboard mode only) ────────────────────────────

def _inject_floating_js_button():
    """
    Inject a truly floating 🤖 button via JavaScript.
    The script runs in an iframe; it uses window.parent to access the Streamlit DOM
    and opens/collapses the sidebar by triggering the native sidebar toggle button.
    """
    components.html(
        """
<script>
(function() {
  // Create floating bot button in the PARENT document (Streamlit app)
  const parent = window.parent.document;

  // Avoid duplicates
  if (parent.getElementById('refundly-bot-btn')) return;

  // ── Badge ──────────────────────────────────────────────────────────────
  const badge = parent.createElement('div');
  badge.id = 'refundly-bot-badge';
  badge.innerHTML = 'Besoin d\'aide ? 💬';
  badge.style.cssText = [
    'position:fixed', 'bottom:98px', 'right:22px', 'z-index:9999',
    'background:#667eea', 'color:white', 'padding:5px 12px',
    'border-radius:20px', 'font-size:12px', 'font-weight:600',
    'box-shadow:0 2px 8px rgba(102,126,234,.4)',
    'pointer-events:none', 'white-space:nowrap',
    'animation:rfBadge 1.2s ease'
  ].join(';');

  // ── Bot button ──────────────────────────────────────────────────────────
  const btn = parent.createElement('button');
  btn.id = 'refundly-bot-btn';
  btn.innerHTML = '🤖';
  btn.title = 'Ouvrir l\'assistant Refundly';
  btn.style.cssText = [
    'position:fixed', 'bottom:28px', 'right:28px', 'z-index:9999',
    'width:64px', 'height:64px', 'border-radius:50%', 'border:none',
    'background:linear-gradient(135deg,#667eea 0%,#764ba2 100%)',
    'color:white', 'font-size:28px', 'cursor:pointer',
    'box-shadow:0 6px 20px rgba(102,126,234,.55)',
    'transition:transform .2s,box-shadow .2s'
  ].join(';');

  btn.onmouseenter = () => {
    btn.style.transform = 'scale(1.12)';
    btn.style.boxShadow = '0 8px 28px rgba(102,126,234,.75)';
  };
  btn.onmouseleave = () => {
    btn.style.transform = 'scale(1)';
    btn.style.boxShadow = '0 6px 20px rgba(102,126,234,.55)';
  };

  // Toggle sidebar on click
  btn.onclick = () => {
    // Try both possible sidebar toggle selectors across Streamlit versions
    const toggle = parent.querySelector('[data-testid="collapsedControl"]')
                || parent.querySelector('[aria-label="Open sidebar"]')
                || parent.querySelector('section[data-testid="stSidebar"] + div button');
    if (toggle) {
      toggle.click();
    }
    // Hide badge after first click
    const b = parent.getElementById('refundly-bot-badge');
    if (b) b.style.display = 'none';
  };

  // Pulse animation
  const style = parent.createElement('style');
  style.textContent = `
    @keyframes rfPulse {
      0%,100% { box-shadow: 0 6px 20px rgba(102,126,234,.55); }
      50%      { box-shadow: 0 6px 30px rgba(102,126,234,.85); }
    }
    @keyframes rfBadge {
      from { opacity:0; transform:translateY(6px); }
      to   { opacity:1; transform:translateY(0); }
    }
    #refundly-bot-btn { animation: rfPulse 3s infinite; }
  `;
  parent.head.appendChild(style);
  parent.body.appendChild(badge);
  parent.body.appendChild(btn);
})();
</script>
        """,
        height=0,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_state(context: str):
    if "bot_messages" not in st.session_state:
        welcome = _welcome_for_context(context)
        st.session_state.bot_messages = [{"role": "assistant", "content": welcome}]


def _handle_message(question: str, context: str):
    st.session_state.bot_messages.append({"role": "user", "content": question})
    response = _get_response(question, context)
    st.session_state.bot_messages.append({"role": "assistant", "content": response})


def _welcome_for_context(context: str) -> str:
    c = context.lower()
    if "boutique" in c or "api" in c:
        return "🏪 Je peux vous guider pour trouver votre clé API. Quelle est votre plateforme ?"
    if "bancaire" in c or "iban" in c:
        return "💳 Des questions sur votre IBAN ou les virements ? Je suis là !"
    if "profil" in c:
        return "👋 Bienvenue sur Refundly ! Posez-moi toutes vos questions."
    return "👋 Bonjour ! Je suis l'assistant Refundly. Comment puis-je vous aider ?"


def _quick_questions(context: str) -> list:
    c = context.lower()
    if "boutique" in c or "api" in c:
        return [
            "Comment trouver ma clé API Shopify ?",
            "C'est sécurisé de donner ma clé API ?",
            "Je n'ai pas de compte développeur Shopify",
        ]
    if "iban" in c or "bancaire" in c:
        return [
            "Où trouver mon IBAN ?",
            "Pourquoi vous avez besoin de mon IBAN ?",
            "Quand je reçois mon remboursement ?",
        ]
    return [
        "Comment fonctionne Refundly ?",
        "Quels transporteurs sont couverts ?",
        "Combien de temps pour un remboursement ?",
    ]


def _get_response(question: str, context: str = "") -> str:
    """Try Gemini via ChatbotManager, fall back to hardcoded answers."""
    try:
        if "chatbot_manager" not in st.session_state:
            from src.ai.chatbot_manager import ChatbotManager
            st.session_state.chatbot_manager = ChatbotManager()
        stream = st.session_state.chatbot_manager.generate_response_stream(
            question, st.session_state.bot_messages[:-1]
        )
        return "".join(stream) or "Je n'ai pas pu générer de réponse, réessayez."
    except Exception:
        fallbacks = {
            "shopify": "Dans votre admin Shopify → **Paramètres → Applications → Développer des applications**. Créez une app 'Refundly' avec les permissions `read_orders`. Votre jeton commence par `shpat_`.",
            "iban": "Votre IBAN se trouve sur votre **relevé de compte** ou dans l'espace 'Mon compte' de votre banque en ligne. Il commence par `FR76` pour une banque française.",
            "sécuri": "Oui, 100 %. Chiffrement AES-256. **Lecture seule** sur vos commandes uniquement. Révocable à tout moment depuis votre admin boutique.",
            "commission": "**20 %** du montant récupéré. Si nous n'obtenons rien, vous ne payez rien.",
            "transporteur": "DHL, Colissimo, Chronopost, UPS, FedEx, DPD, GLS, TNT, Mondial Relay et d'autres.",
            "remboursement": "En moyenne **4 à 8 semaines** selon le transporteur. Email de confirmation à chaque étape.",
        }
        q = question.lower()
        for key, resp in fallbacks.items():
            if key in q:
                return resp
        return "Je rencontre une difficulté technique. N'hésitez pas à reformuler votre question."
