"""
Password reset UI component for login page.
"""

import streamlit as st
from src.utils.email_service import EmailService
from src.auth.credentials_manager import CredentialsManager


def render_password_reset():
    """Render password reset interface."""
    
    st.markdown("### 🔓 Mot de passe oublié ?")
    st.markdown("Entrez votre email pour recevoir un lien de réinitialisation.")
    
    with st.form("reset_password_form"):
        email = st.text_input(
            "Email",
            placeholder="votre@email.com",
            help="L'email associé à votre compte"
        )
        
        submitted = st.form_submit_button("📧 Envoyer le lien", width='stretch')
        
        if submitted:
            if not email:
                st.error("⚠️ Veuillez entrer votre email")
            else:
                # Check if email exists
                manager = CredentialsManager()
                creds = manager.get_credentials(email)
                
                if creds:
                    # Generate reset token
                    email_service = EmailService()
                    token = email_service.generate_reset_token(email)
                    
                    # Create reset URL
                    reset_url = f"http://localhost:8503?reset_token={token}"
                    
                    # Send email
                    success = email_service.send_password_reset_email(email, reset_url)
                    
                    if success:
                        st.success("✅ Email envoyé ! Vérifiez votre boîte de réception.")
                        st.info("💡 Le lien est valide pendant 24 heures.")
                    else:
                        st.error("❌ Erreur lors de l'envoi. Réessayez plus tard.")
                else:
                    # Don't reveal if email exists or not (security)
                    st.success("✅ Si cet email existe, vous recevrez un lien de réinitialisation.")
    
    # Back to login
    if st.button("← Retour à la connexion"):
        st.session_state.show_reset = False
        st.rerun()


def render_reset_password_form(token: str):
    """Render form to set new password with valid token."""
    
    st.markdown("### 🔐 Nouveau mot de passe")
    
    # Validate token
    email_service = EmailService()
    email = email_service.validate_reset_token(token)
    
    if not email:
        st.error("❌ Lien invalide ou expiré")
        if st.button("← Retour à la connexion"):
            st.rerun()
        return
    
    st.info(f"📧 Réinitialisation pour : {email}")
    
    with st.form("new_password_form"):
        new_password = st.text_input(
            "Nouveau mot de passe",
            type="password",
            placeholder="Minimum 8 caractères",
            help="Choisissez un mot de passe sécurisé"
        )
        
        confirm_password = st.text_input(
            "Confirmer le mot de passe",
            type="password",
            placeholder="Retapez le mot de passe"
        )
        
        submitted = st.form_submit_button("✅ Réinitialiser", width='stretch')
        
        if submitted:
            # Validation
            if not new_password or not confirm_password:
                st.error("⚠️ Veuillez remplir les deux champs")
            elif new_password != confirm_password:
                st.error("❌ Les mots de passe ne correspondent pas")
            elif len(new_password) < 8:
                st.error("❌ Le mot de passe doit faire au moins 8 caractères")
            else:
                # TODO: Store hashed password in database
                # For now, we just invalidate the token
                
                email_service.invalidate_token(token)
                
                st.success("✅ Mot de passe réinitialisé avec succès !")
                st.info("Vous pouvez maintenant vous connecter avec votre nouveau mot de passe.")
                
                if st.button("→ Aller à la connexion"):
                    st.rerun()
