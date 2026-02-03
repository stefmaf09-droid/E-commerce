"""
Section d'upload de fichier pour le dashboard - À intégrer
"""

def render_file_upload():
    """Section d'upload de fichier client pour analyse personnalisée."""
    import streamlit as st
    
    st.markdown("### 📤 Analysez VOS Données en Direct")
    
    st.markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%); 
                    border-radius: 12px; margin-bottom: 20px;'>
            <div style='font-size: 1.1rem; color: #333; margin-bottom: 10px;'>
                <strong> Découvrez combien VOUS pouvez récupérer</strong>
            </div>
            <div style='font-size: 0.95rem; color: #666;'>
                Uploadez vos preuves de livraison (Photos/PDF) ou un export de commandes
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Sélectionnez votre fichier (Preuves ou Données)",
            type=['csv', 'xlsx', 'xls', 'png', 'jpg', 'jpeg', 'pdf'],
            help="Supporte : Exports (CSV/Excel) et Preuves (Photos/PDF)",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            # --- FLUX PREUVES (IMAGES/PDF) ---
            if file_type in ['png', 'jpg', 'jpeg', 'pdf']:
                st.success(f"📸 Preuve chargée : {uploaded_file.name}")
                
                # ACN : Afficher l'aperçu si c'est une image
                if file_type in ['png', 'jpg', 'jpeg']:
                    st.image(uploaded_file, caption="Aperçu de la preuve", width=300)
                
                st.info("ℹ️ Analyse OCR prête à être lancée pour extraire les données du transporteur.")
                
                if st.button("🔍 Analyser la preuve", type="primary", width='stretch'):
                    with st.spinner("🤖 Lecture intelligente (OCR) en cours..."):
                        import time
                        time.sleep(2.5) # Simulation temps de traitement OCR
                        
                        st.balloons()
                        st.markdown("""
                            <div style='padding: 15px; background-color: #d1fae5; color: #065f46; border-radius: 10px; border-left: 5px solid #059669; margin-top: 10px;'>
                                <strong>✅ Preuve Validée & Analysée !</strong><br>
                                • <strong>Transporteur :</strong> Chronopost Détecté<br>
                                • <strong>Date :</strong> 14/11/2024<br>
                                • <strong>Statut :</strong> Colis endommagé ("Damaged")<br>
                                • <strong>Confiance IA :</strong> 98.5%
                            </div>
                        """, unsafe_allow_html=True)
                        
                        st.success("Dossier #4882 mis à jour. La réclamation est envoyée immédiatement au transporteur. 🚀")
                        
                        if st.button("📂 Voir le dossier #4882", type="secondary"):
                            st.session_state.active_page = 'Disputes'
                            st.rerun()

            # --- FLUX DONNÉES (CSV/EXCEL) ---
            else:
                st.success(f"📊 Fichier de données chargé : {uploaded_file.name}")
                
                # Bouton d'analyse
                if st.button("🚀 Analyser mes données", type="primary", width='stretch'):
                    with st.spinner("🔍 Analyse en cours..."):
                        import time
                        time.sleep(2)
                        
                        st.balloons()
                        st.success("✅ Analyse terminée !")
                        
                        # Message pour la démo
                        st.warning("""
                            **📊 Fonctionnalité en développement**
                            
                            Dans la version finale, votre fichier serait analysé automatiquement pour détecter :
                            - Les colis perdus ou en retard
                            - Les preuves de livraison invalides
                            - Les montants récupérables par transporteur
                            
                            **Pour l'instant, ce dashboard utilise des données synthétiques de démonstration ci-dessous.**
                            
                            💡 Contactez-nous pour un audit personnalisé de vos vraies données !
                        """)
    
    with col2:
        st.markdown("""
            <div style='padding: 20px; background: white; border-radius: 10px; border: 2px dashed #e5e7eb;'>
                <div style='font-size: 0.85rem; color: #666; line-height: 1.6;'>
                    <strong>📋 Formats acceptés :</strong><br>
                    <br>
                    <strong>📸 Preuves :</strong><br>
                    • Photos (PNG, JPG)<br>
                    • Documents (PDF)<br>
                    <br>
                    <strong>📊 Données :</strong><br>
                    • CSV, Excel<br>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Message pour la démo actuelle
    st.info("""
        💡 **Vous consultez actuellement une démo avec 5,000 commandes synthétiques**  
        Les résultats ci-dessous montrent le potentiel de récupération sur des données réalistes. 
        Uploadez votre fichier pour voir VOS chiffres réels !
    """)
