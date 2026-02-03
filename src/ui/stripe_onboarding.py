
import streamlit as st
import os
from src.payments.stripe_manager import StripeManager
from src.database.database_manager import get_db_manager

def render_stripe_onboarding(client_email: str):
    """Affiche l'interface d'onboarding Stripe Connect."""
    st.markdown("---")
    st.subheader("💳 Automatisation Stripe Connect")
    st.info("""
        🚀 **Passez au niveau supérieur !**  
        Activez Stripe Connect pour recevoir vos fonds automatiquement dès qu'un litige est récupéré.
        - **Zéro délai** : Virement automatique sur votre compte.
        - **Transparence** : Suivi des commissions en temps réel.
        - **Sécurité** : Gestion sécurisée par Stripe.
    """)
    
    db = get_db_manager()
    client = db.get_client(email=client_email)
    
    if not client:
        st.error("Impossible de récupérer les informations client.")
        return

    stripe_mgr = StripeManager()
    
    # État actuel
    stripe_id = client.get('stripe_connect_id')
    status = client.get('stripe_onboarding_status', 'pending')
    
    if not stripe_id:
        st.write("### 🏁 Commencer l'onboarding")
        st.write("Veuillez sélectionner le pays de domiciliation de votre entreprise :")
        
        # Liste des pays supportés par Stripe Express (simplifiée)
        country_options = {
            "France": "FR",
            "Hong Kong": "HK",
            "Singapore": "SG",
            "United Kingdom": "GB",
            "United States": "US",
            "Germany": "DE"
        }
        selected_country_name = st.selectbox("Pays", list(country_options.keys()))
        selected_country_code = country_options[selected_country_name]
        
        st.write("Vous allez être redirigé vers Stripe pour créer votre compte professionnel connecté.")
        
        if st.button("🚀 Créer mon compte Stripe Connect", type="primary"):
            try:
                account_id = stripe_mgr.create_connect_account(client_email, country=selected_country_code)
                
                # Sauvegarder l'ID dans la BDD
                db.update_client(client['id'], stripe_connect_id=account_id)
                
                # Générer le lien
                # En production, return_url pointerait vers une page de succès
                onboarding_url = stripe_mgr.generate_onboarding_link(
                    account_id=account_id,
                    refresh_url="https://votre-domaine.com/refresh", 
                    return_url="https://votre-domaine.com/complete"
                )
                
                st.success("✅ Compte Stripe créé !")
                st.markdown(f"[➡️ Cliquer ici pour finaliser l'onboarding sur Stripe]({onboarding_url})")
                st.info("Une fois l'onboarding terminé sur Stripe, votre statut sera mis à jour automatiquement.")
                
            except Exception as e:
                st.error(f"Erreur lors de la création du compte Stripe : {e}")
    
    elif status == 'pending':
        st.warning("⏳ **Onboarding en cours**")
        st.write(f"ID Stripe : `{stripe_id}`")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Vérifier mon statut", key="check_stripe_status"):
                try:
                    stripe_status = stripe_mgr.get_account_status(stripe_id)
                    if stripe_status['details_submitted']:
                        db.update_client(client['id'], stripe_onboarding_status='active', stripe_onboarding_completed=1)
                        st.success("🎉 Votre compte Stripe est maintenant actif !")
                        st.rerun()
                    else:
                        st.info("L'onboarding n'est pas encore finalisé sur Stripe.")
                        st.write("**Requis :** " + ", ".join(stripe_status['requirements']) if stripe_status['requirements'] else "Aucun")
                except Exception as e:
                    st.error(f"Erreur : {e}")
        
        with col2:
            # Relancer le lien si perdu
            if st.button("🔗 Régénérer le lien d'onboarding"):
                onboarding_url = stripe_mgr.generate_onboarding_link(
                    account_id=stripe_id,
                    refresh_url="https://votre-domaine.com/refresh",
                    return_url="https://votre-domaine.com/complete"
                )
                st.markdown(f"[➡️ Lien d'onboarding]({onboarding_url})")
                
    elif status == 'active':
        st.success("✅ **Stripe Connect Actif**")
        st.write(f"ID Stripe : `{stripe_id}`")
        st.info("Vos virements sont désormais automatisés via Stripe Connect.")
        
        if st.button("💼 Accéder au Dashboard Stripe Express"):
            # En théorie Stripe permet de générer un Login Link pour Express
            st.info("Redirection vers votre interface Stripe Express...")
            # stripe.Account.create_login_link(stripe_id)
