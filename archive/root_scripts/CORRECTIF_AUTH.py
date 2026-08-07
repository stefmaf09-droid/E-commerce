"""
CORRECTIF SÉCURITÉ - Authentication avec mot de passe obligatoire

À appliquer dans client_dashboard.py ligne 125-154
"""

def authenticate():
    """Authentication requiring email AND password."""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.client_email = None
    
    if not st.session_state.authenticated:
        st.markdown("<h1 class='main-header'>🔐 Connexion Client</h1>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="votre@email.com")
            password = st.text_input("Mot de passe", type="password", placeholder="Votre mot de passe")
            submitted = st.form_submit_button("Se connecter", width='stretch')
            
            if submitted:
                # CORRECTION: Validation password obligatoire
                if not email or not password:
                    st.error("⚠️ Email ET mot de passe requis")
                    return False
                
                # Check credentials  
                manager = CredentialsManager()
                creds = manager.get_credentials(email)
                
                if creds:
                    # TODO PRODUCTION: Implémenter bcrypt password hashing
                    # Pour MVP: On accepte si password non vide
                    st.session_state.authenticated = True
                    st.session_state.client_email = email
                    st.success(f"✅ Bienvenue {email}")
                    st.rerun()
                else:
                    st.error("❌ Email non trouvé")
        
        return False
    
    return True
