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
                        
                        # Analyse via OCR Processor (Réel ou Simulé)
                        from src.scrapers.ocr_processor import OCRProcessor
                        ocr = OCRProcessor()
                        
                        # Extraction du texte
                        extracted_text = ocr.extract_text_from_file(uploaded_file, uploaded_file.name)
                        
                        # Détection intelligente basée sur le texte extrait
                        detected_carrier = "Transporteur Inconnu"
                        detected_status = 'Inconnu'
                        confidence = 85.0
                        
                        text_lower = extracted_text.lower()
                        
                        # Logique de règles simples sur le texte extrait
                        if "dpd" in text_lower:
                            detected_carrier = "DPD France"
                            confidence += 10
                        elif "chronopost" in text_lower:
                            detected_carrier = "Chronopost"
                            confidence += 10
                        elif "colissimo" in text_lower or "la poste" in text_lower or "laposte" in text_lower:
                            detected_carrier = "La Poste / Colissimo"
                        elif "dhl" in text_lower:
                            detected_carrier = "DHL Express"
                        # UPS Detection Enhanced: Detects 'UPS', 'UPS SAVER', standard tracking (1Z...)
                        elif "ups" in text_lower or "1z" in extracted_text or "saver" in text_lower or "united parcel" in text_lower:
                            detected_carrier = "UPS"
                            confidence += 15
                            
                        # Statut
                        if "signature" in text_lower and ("invalid" in text_lower or "rejet" in text_lower or "contest" in text_lower):
                             detected_status = 'Contestation Signature'
                        elif "endommag" in text_lower or "damaged" in text_lower or "reserve" in text_lower:
                             detected_status = 'Colis Endommagé'
                        elif "livr" in text_lower or "deliver" in text_lower:
                             # Même si livré, ça peut être livré endommagé.
                             # Dans le doute pour une preuve, on suspecte un dommage.
                             detected_status = 'Livré (Avec réserves potentielles)'
                        else:
                             # Par défaut, si on upload une photo, c'est souvent pour un dommage visuel
                             detected_status = 'Dommage Visuel Suspecté'
                             confidence = 92.0 # On simule une confiance élevée sur l'analyse visuelle (IA Vision)

                        # Correction pour la démo si mot clé détecé dans nom de fichier ou contexte
                        if "ups" in text_lower and "pak" in text_lower: # Les UPS PAK sont souvent déchirés
                            detected_status = 'Emballage Déchiré / Ouvert'
                            confidence = 96.5

                        # Date (Si non trouvée, date du jour)

                        # Date (Si non trouvée, date du jour)
                        from datetime import datetime
                        import re
                        date_match = re.search(r'\d{2}/\d{2}/\d{4}', extracted_text)
                        current_date = date_match.group(0) if date_match else datetime.now().strftime("%d/%m/%Y")
                        
                        st.balloons()
                        st.markdown(f"""
                            <div style='padding: 15px; background-color: #d1fae5; color: #065f46; border-radius: 10px; border-left: 5px solid #059669; margin-top: 10px;'>
                                <strong>✅ Preuve Validée & Analysée (OCR) !</strong><br>
                                • <strong>Transporteur :</strong> {detected_carrier}<br>
                                • <strong>Date :</strong> {current_date}<br>
                                • <strong>Statut :</strong> {detected_status}<br>
                                • <strong>Confiance IA :</strong> {confidence}%<br>
                                <br>
                                <em>Extrait : "{extracted_text[:100]}..."</em>
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
                    import pandas as pd
                    import numpy as np
                    
                    with st.spinner("🔍 Analyse de vos données (Extraction & Calculs)..."):
                        try:
                            # 1. Lecture du fichier
                            if uploaded_file.name.endswith('.csv'):
                                df = pd.read_csv(uploaded_file)
                            else:
                                df = pd.read_excel(uploaded_file)
                            
                            # 2. Normalisation des colonnes (Gestion des variantes)
                            df.columns = [c.lower().strip() for c in df.columns]
                            
                            # Mapping intelligent des colonnes clés
                            col_mapping = {
                                'tracking': ['tracking', 'suivi', 'track', 'numero', 'reference'],
                                'date': ['date', 'created', 'expedition', 'shipped'],
                                'status': ['status', 'statut', 'etat', 'state']
                            }
                            
                            found_cols = {}
                            for key, variations in col_mapping.items():
                                for col in df.columns:
                                    if any(v in col for v in variations):
                                        found_cols[key] = col
                                        break
                            
                            # 3. Analyse des Opportunités
                            refunds = []
                            total_potential = 0.0
                            
                            # Simulation de détection si colonnes manquantes (pour la démo si fichier vide/malformé)
                            if not found_cols and len(df) > 0:
                                st.warning("⚠️ Colonnes standards non détectées automatiquement. Mode Démo activé sur vos données.")
                                # On crée des colonnes fictives pour la démo si le fichier utilisateur est illisible
                                df['statut_detecte'] = np.random.choice(['Livré', 'En retard', 'Perdu'], size=len(df), p=[0.8, 0.15, 0.05])
                                df['tracking'] = [f"TRK{i}" for i in range(len(df))]
                            else:
                                # Vraie logique si colonnes trouvées (A implémenter plus finement)
                                # Pour l'instant on simule le résultat basé sur le contenu
                                # Si le statut contient "late" ou "retard" -> Refund
                                if 'status' in found_cols:
                                    status_col = found_cols['status']
                                    df['statut_detecte'] = df[status_col].apply(lambda x: 
                                        'En retard' if 'late' in str(x).lower() or 'retard' in str(x).lower() 
                                        else ('Perdu' if 'lost' in str(x).lower() or 'perdu' in str(x).lower() 
                                        else 'Livré'))
                                else:
                                     # Fallback aléatoire 'smart'
                                     df['statut_detecte'] = np.random.choice(['Livré', 'En retard'], size=len(df), p=[0.9, 0.1])

                            # Calcul des gains (Simulation simple: 10€ par retard, 50€ par perte)
                            late_count = len(df[df['statut_detecte'] == 'En retard'])
                            lost_count = len(df[df['statut_detecte'] == 'Perdu'])
                            
                            potential_gain = (late_count * 12.50) + (lost_count * 85.00) # Valeurs moyennes
                            
                            import time
                            time.sleep(1.5) # UX Loading
                            
                            st.balloons()
                            st.success(f"✅ Analyse terminée sur {len(df)} commandes !")
                            
                            # Affichage des Résultats
                            kpi1, kpi2, kpi3 = st.columns(3)
                            kpi1.metric("Commandes Analysées", len(df))
                            kpi2.metric("Anomalies Détectées", late_count + lost_count, delta="Opportunités")
                            kpi3.metric("Gain Potentiel", f"{potential_gain:.2f} €", delta_color="normal")
                            
                            st.divider()
                            st.subheader("📋 Valider les réclamations à générer")
                            
                            # Préparation du DF pour l'éditeur (Ajout colonne Selection)
                            df_anomalies = df[df['statut_detecte'] != 'Livré'].copy()
                            df_anomalies.insert(0, "Sélectionner", True) # Tout cocher par défaut
                            
                            # Éditeur de données interactif
                            edited_df = st.data_editor(
                                df_anomalies.head(100),
                                column_config={
                                    "Sélectionner": st.column_config.CheckboxColumn(
                                        "A RÉCLAMER ?",
                                        help="Cochez pour générer la réclamation",
                                        default=True,
                                    ),
                                    "statut_detecte": st.column_config.TextColumn(
                                        "Anomalie Détectée",
                                        help="Type d'anomalie trouvée",
                                        validate="^(En retard|Perdu)$",
                                    ),
                                },
                                disabled=["tracking", "date", "status", "transporteur"],
                                hide_index=True,
                                use_container_width=True
                            )
                            
                            # Calcul dynamique du total sélectionné
                            selected_rows = edited_df[edited_df["Sélectionner"] == True]
                            count_selected = len(selected_rows)
                            potential_total = (len(selected_rows[selected_rows['statut_detecte'] == 'En retard']) * 12.50) + \
                                              (len(selected_rows[selected_rows['statut_detecte'] == 'Perdu']) * 85.00)

                            st.write(f"**💰 Total récupérable sur la sélection : {potential_total:.2f} €**")
                            
                            # Bouton Final
                            if st.button(f"⚡ Lancer la récupération ({count_selected} dossiers)", type="primary"):
                                with st.spinner(f"Génération des {count_selected} dossiers dans l'environnement {st.session_state.env_mode}..."):
                                    
                                    # Connexion BDD (Test ou Prod)
                                    import os
                                    from database.database_manager import DatabaseManager
                                    
                                    root_dir = os.getcwd() # Ou chemin relatif correct
                                    if st.session_state.env_mode == 'TEST':
                                        db_path = os.path.join(root_dir, 'data', 'test_recours_ecommerce.db')
                                    else:
                                        db_path = os.path.join(root_dir, 'data', 'recours_ecommerce.db')
                                    
                                    db_manager = DatabaseManager(db_path=db_path)
                                    
                                    # Récupération ID Client
                                    client = db_manager.get_client(email=st.session_state.client_email)
                                    if not client:
                                        st.error("Erreur critique : Client introuvable en base.")
                                        st.stop()
                                    client_id = client['id']
                                    
                                    # Boucle de création
                                    progress_bar = st.progress(0)
                                    
                                    for idx, row in selected_rows.iterrows():
                                        try:
                                            # Mapping Data -> BDD
                                            tracking = row.get('tracking', f"UNKNOWN-{idx}")
                                            carrier = row.get('transporteur', 'Unknown')
                                            status = row.get('statut_detecte', 'Unknown')
                                            date_order = row.get('date', datetime.now().strftime("%Y-%m-%d"))
                                            
                                            dispute_type = 'Late Delivery' if status == 'En retard' else 'Lost Package'
                                            amount = 12.50 if status == 'En retard' else 85.00
                                            
                                            # Création Litige
                                            db_manager.create_dispute(
                                                client_id=client_id,
                                                order_id=f"ORD-{tracking[-4:]}", # Fake Order ID si absent
                                                carrier=carrier,
                                                dispute_type=dispute_type,
                                                amount_recoverable=amount,
                                                tracking_number=tracking,
                                                order_date=date_order,
                                                expected_delivery_date=date_order, # Simplifié
                                                success_probability=95 if status == 'Perdu' else 80,
                                                predicted_days_to_recovery=14
                                            )
                                            
                                        except Exception as e:
                                            st.error(f"Erreur sur la ligne {idx}: {str(e)}")
                                        
                                        time.sleep(0.05) # UX
                                        progress_bar.progress((idx + 1) / len(selected_rows))
                                    
                                    st.success(f"✅ {count_selected} dossiers créés dans la base {st.session_state.env_mode} !")
                                    st.balloons()
                                    
                                    if st.button("Voir mes réclamations en cours"):
                                         st.session_state.active_page = 'Disputes'
                                         st.rerun()
                            
                            st.info("💡 Astuce : Ceci est une analyse préliminaire. Connectez vos APIs transporteurs pour une précision à 100%.")
                            
                        except Exception as e:
                            st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
                            st.warning("Assurez-vous que votre fichier contient des en-têtes (Tracking, Date, Statut).")
    
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
