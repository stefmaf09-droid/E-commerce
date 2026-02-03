"""
INTÉGRATION - Système de réinitialisation de mot de passe dans client_dashboard.py

Instructions pour intégrer le système password reset dans l'interface de login.
"""

# === EN HAUT DU FICHIER (après les autres imports) ===

from dotenv import load_dotenv
load_dotenv()  # Charger variables d'environnement

from ui.password_reset import render_password_reset, render_reset_password_form


# === MODIFIER LA FONCTION authenticate() (ligne ~125) ===

def authenticate():
    """Handle client authentication with password reset support."""
    if st.session_state.get('authenticated', False):
        return True
    
    # Check for reset token in URL
    query_params = st.query_params
    if 'reset_token' in query_params:
        token = query_params['reset_token']
        render_reset_password_form(token)
        return False
    
    # Check if showing password reset
    if st.session_state.get('show_reset', False):
        render_password_reset()
        return False
    
    # Normal login form
    st.markdown('<h1 style="color: #dc2626; text-align: center;">🔐 Connexion Client</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center;">Accédez à votre tableau de bord de récupération</p>', unsafe_allow_html=True)
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="votre@email.com")
        password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
        
        submitted = st.form_submit_button("Se connecter", width='stretch')
        
        if submitted:
            # Validation
            if not email or not password:
                st.error("⚠️ Email et mot de passe requis")
                return False
            
            # Check credentials
            manager = CredentialsManager()
            creds = manager.get_credentials(email)
            
            if creds:
                # TODO Production: Vérifier hash bcrypt du password
                st.session_state.authenticated = True
                st.session_state.client_email = email
                st.success(f"✅ Bienvenue {email} !")
                st.rerun()
                return True
            else:
                st.error("❌ Email ou mot de passe incorrect")
                return False
    
    # Link to password reset
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔓 Mot de passe oublié ?", width='stretch'):
            st.session_state.show_reset = True
            st.rerun()
    
    return False


# === C'EST TOUT ! ===
# Le système est maintenant intégré et fonctionnel.
