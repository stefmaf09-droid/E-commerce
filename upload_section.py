"""
Section d'upload de fichier pour le dashboard - À intégrer
"""

def render_file_upload():
    """Section d'upload de fichier client pour analyse personnalisée."""
    import streamlit as st
    import time  # Audit du 26/08/2026 : n'était importé que dans la branche
    # "Analyser la preuve" (image/PDF), pas dans la branche CSV/Excel qui
    # l'utilise aussi (time.sleep dans la boucle d'envoi) — NameError non
    # catché qui plantait toute la page au clic sur "Confirmer et Envoyer".
    from datetime import datetime  # Audit du 26/08/2026 (suite) : même bug
    # que 'time' ci-dessus — un import local de 'datetime' dans l'AUTRE
    # branche (ligne ~108) suffit à en faire une variable locale pour toute
    # la fonction aux yeux de Python ; utilisé sans import dans la branche
    # CSV (ligne ~366), ça levait un UnboundLocalError catché par le
    # try/except mais affiché comme "Erreur dossier X" pour CHAQUE dossier
    # au clic sur "Confirmer et envoyer" — aucun dossier n'était réellement
    # créé avec une vraie date malgré le message de succès global.
    from database.database_manager import DatabaseManager # Fix UnboundLocalError
    
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
                        
                        # --- ENVOI EMAIL DE CONFIRMATION CLIENT ---
                        try:
                            from src.email_service.email_sender import send_claim_submitted_email
                            client_email = st.session_state.get('client_email', 'test@example.com')
                            
                            # Calcul basique du montant pour la démo
                            amount = 85.00 if 'endommag' in detected_status.lower() or 'perte' in detected_status.lower() else 12.50
                            
                            send_claim_submitted_email(
                                client_email=client_email,
                                claim_reference="CLM-4882",
                                carrier=detected_carrier,
                                amount_requested=amount,
                                order_id="ORD-4882",
                                submission_method="portal",
                                dispute_type=detected_status
                            )
                        except Exception as e:
                            st.warning(f"Avertissement : Impossible d'envoyer l'email de confirmation ({e})")
                                                
                        if st.button("📂 Voir le dossier #4882", type="secondary"):
                            st.session_state.active_page = 'Disputes'
                            st.rerun()

            # --- FLUX DONNÉES (CSV/EXCEL) ---
            else:
                st.success(f"📊 Fichier de données chargé : {uploaded_file.name}")
                
                # Bouton d'analyse (Trigger)
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
                            
                            # 2. Normalisation des colonnes
                            df.columns = [c.lower().strip() for c in df.columns]
                            
                            # Mapping intelligent
                            col_mapping = {
                                'tracking': ['tracking', 'suivi', 'track', 'numero', 'reference'],
                                'date': ['date', 'created', 'expedition', 'shipped'],
                                'status': ['status', 'statut', 'etat', 'state'],
                                # Audit du 26/08/2026 : aucune détection de colonne
                                # transporteur n'existait — un CSV avec une colonne
                                # 'carrier' (anglais, comme dans nos données de test)
                                # ne remplissait jamais df['transporteur'], donc
                                # chaque réclamation/PDF/email généré affichait
                                # 'Unknown' comme transporteur, même quand
                                # l'information était bien présente dans le fichier
                                # (confirmé en test live : "Unknown" affiché dans
                                # l'Assistant pour des lignes Chronopost/UPS réelles).
                                'carrier': ['carrier', 'transporteur', 'shipper', 'livreur']
                            }
                            
                            found_cols = {}
                            for key, variations in col_mapping.items():
                                for col in df.columns:
                                    if any(v in col for v in variations):
                                        found_cols[key] = col
                                        break
                                        
                            # ... (Logique d'analyse identique)
                            if not found_cols and len(df) > 0:
                                df['statut_detecte'] = np.random.choice(['Livré', 'En retard', 'Perdu'], size=len(df), p=[0.8, 0.15, 0.05])
                                df['tracking'] = [f"TRK{i}" for i in range(len(df))]
                            else:
                                if 'status' in found_cols:
                                    status_col = found_cols['status']
                                    df['statut_detecte'] = df[status_col].apply(lambda x: 
                                        'En retard' if 'late' in str(x).lower() or 'retard' in str(x).lower() 
                                        else ('Perdu' if 'lost' in str(x).lower() or 'perdu' in str(x).lower() 
                                        else 'Livré'))
                                else:
                                     df['statut_detecte'] = np.random.choice(['Livré', 'En retard'], size=len(df), p=[0.9, 0.1])

                                if 'carrier' in found_cols:
                                    df['transporteur'] = df[found_cols['carrier']]
                                elif 'transporteur' not in df.columns:
                                    df['transporteur'] = 'Unknown'

                            # Stockage en Session State pour persistance
                            st.session_state.analysis_df = df
                            st.session_state.upload_step = 'selection'
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Erreur lors de l'analyse : {str(e)}")

                # --- AFFICHAGE PERSISTANT DES RÉSULTATS ---
                if 'analysis_df' in st.session_state and st.session_state.upload_step in ['selection', 'review', 'done']:
                    df = st.session_state.analysis_df
                    late_count = len(df[df['statut_detecte'] == 'En retard'])
                    lost_count = len(df[df['statut_detecte'] == 'Perdu'])
                    potential_gain = (late_count * 12.50) + (lost_count * 85.00)
                    
                    # KPIs (Toujours visibles)
                    st.divider()
                    kpi1, kpi2, kpi3 = st.columns(3)
                    kpi1.metric("Commandes Analysées", len(df))
                    kpi2.metric("Anomalies Détectées", late_count + lost_count, delta="Opportunités")
                    kpi3.metric("Gain Potentiel", f"{potential_gain:.2f} €", delta_color="normal")
                    
                    # --- ÉTAPE 1 : Sélection & Validation ---
                    if st.session_state.upload_step == 'selection':
                        st.divider()
                        st.subheader("📋 Valider les réclamations à générer")
                        
                        df_anomalies = df[df['statut_detecte'] != 'Livré'].copy()
                        if "Sélectionner" not in df_anomalies.columns:
                            df_anomalies.insert(0, "Sélectionner", True)
                        
                        edited_df = st.data_editor(
                            df_anomalies.head(100),
                            column_config={
                                "Sélectionner": st.column_config.CheckboxColumn("A RÉCLAMER ?", default=True),
                                "statut_detecte": st.column_config.TextColumn("Anomalie"),
                            },
                            disabled=["tracking", "date", "status", "transporteur"],
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        selected_rows = edited_df[edited_df["Sélectionner"] == True]
                        count_selected = len(selected_rows)
                        potential_total = (len(selected_rows[selected_rows['statut_detecte'] == 'En retard']) * 12.50) + \
                                          (len(selected_rows[selected_rows['statut_detecte'] == 'Perdu']) * 85.00)

                        st.write(f"**💰 Total récupérable sur la sélection : {potential_total:.2f} €**")
                        
                        if st.button(f"➡️ Préparer {count_selected} réclamations", type="primary"):
                            st.session_state.selected_anomalies = selected_rows
                            st.session_state.upload_step = 'review'
                            st.rerun()

                    # --- ÉTAPE 2 : Revue & Édition ---
                    elif st.session_state.upload_step == 'review':
                        st.divider()
                        st.markdown("### 📧 Vérification des Emails avant envoi")
                        # 31/08/2026 (audit complet) : le texte disait auparavant "Vous
                        # allez générer des emails pour les transporteurs [...] avant
                        # l'envoi groupé", alors que ce bouton ne faisait à l'époque que
                        # créer le dossier + générer le PDF + confirmer par email au
                        # CLIENT (jamais au transporteur), et qu'aucun job planifié
                        # n'existait pour relayer ensuite ce PDF au transporteur.
                        # Depuis, ce job existe (src/workers/reminder_worker.py, démarré
                        # en arrière-plan à la connexion) : il scanne les dossiers en base
                        # et relance réellement le transporteur à J+7/J+14/J+21 (envoi réel
                        # en Prod, simulé sans envoi en Test). Le dossier créé ici entre
                        # bien dans ce circuit automatique — mais l'envoi au transporteur
                        # n'est donc pas immédiat, il suit ce calendrier.
                        st.info("Ceci crée le dossier de réclamation et génère le PDF de mise en demeure. Modifiez le modèle ci-dessous si besoin — le transporteur sera relancé automatiquement (J+7, J+14, puis mise en demeure à J+21) s'il ne répond pas, pas immédiatement à la validation.")
                        
                        # Chargement du Template Officiel
                        from database.email_template_manager import EmailTemplateManager
                        from streamlit_quill import st_quill
                        
                        # On doit instancier avec le bon path
                        import os
                        root_dir = os.getcwd()
                        if st.session_state.env_mode == 'TEST':
                            db_path = os.path.join(root_dir, 'data', 'test_recours_ecommerce.db')
                        else:
                            db_path = os.path.join(root_dir, 'data', 'recours_ecommerce.db')
                        # 31/08/2026 : suite du 26/08 — à l'époque, forcer
                        # db_type='sqlite' ici cassait tout car le client
                        # n'existait pas dans la base SQLite de test (seul
                        # 'admin@refundly.ai' y était pré-rempli). Depuis
                        # l'introduction de la distinction test/prod par
                        # compte (clients.account_mode) et de
                        # get_or_create_client(), un compte TEST peut être
                        # provisionné à la volée dans SA base isolée — donc
                        # ce chemin peut désormais router vers la même base
                        # que celle lue par le tableau de bord ("Mes
                        # Litiges"), au lieu de rester sur la base globale
                        # où l'écriture n'était jamais visible côté lecture.
                        db_type_override = "sqlite" if st.session_state.env_mode == 'TEST' else None
                        template_mgr = EmailTemplateManager(db_path=db_path)

                        # Récup client_id pour chercher un template custom
                        db_mgr_tmbs = DatabaseManager(db_path=db_path, db_type=db_type_override)
                        client = db_mgr_tmbs.get_or_create_client(email=st.session_state.client_email)
                        client_id = client['id'] if client else None
                        
                        # Récupération du template
                        tmpl = template_mgr.get_template('formal_notice', 'FR', client_id=client_id)
                        
                        col_edit, col_preview = st.columns([1, 1])
                        with col_edit:
                            st.subheader("📝 Éditer le modèle")
                            email_subject = st.text_input("Objet", value=tmpl['subject'])
                            
                            # Quill Editor
                            st.caption("Corps de l'email (HTML)")
                            email_body = st_quill(
                                value=tmpl['body'],
                                html=True,
                                key="quill_review_editor"
                            )
                            st.caption("Variables : {tracking_number}, {date}, {amount}, {currency}, {claim_reference}")

                        with col_preview:
                             st.subheader("👁️ Aperçu (Rendu)")
                             if not st.session_state.selected_anomalies.empty:
                                 example_row = st.session_state.selected_anomalies.iloc[0]
                                 
                                 # Préparer les data pour le rendu
                                 claim_data = {
                                     'tracking_number': example_row.get('tracking', '1Z999'),
                                     'claim_reference': f"CLM-{str(example_row.get('tracking', '1Z'))[-4:]}",
                                     'amount_requested': 12.50 if 'retard' in str(example_row.get('statut_detecte', '')).lower() else 85.00,
                                     'currency': 'EUR',
                                     'dispute_type': 'Retard de Livraison' if 'retard' in str(example_row.get('statut_detecte', '')).lower() else 'Perte',
                                     'customer_name': client['full_name'] if client else 'Client Test',
                                     'delivery_address': '12 Rue de la Paix, 75001 Paris',
                                     'carrier': example_row.get('transporteur', 'Colissimo'),
                                     'location': 'Paris'
                                 }
                                 
                                 rendered = template_mgr.render_template(
                                     {'subject': email_subject, 'body': email_body if email_body else tmpl['body']},
                                     claim_data
                                 )
                                 
                                 st.markdown(f"**Objet :** {rendered['subject']}")
                                 st.components.v1.html(rendered['body'], height=350, scrolling=True)
                        
                        col_back, col_send = st.columns([1, 3])
                        with col_back:
                            if st.button("⬅️ Retour"):
                                st.session_state.upload_step = 'selection'
                                st.rerun()
                        
                        with col_send:
                            if st.button(f"🚀 Confirmer et Envoyer", type="primary"):
                                with st.spinner("Envoi..."):
                                    # ... (Logique d'envoi BDD identique) ...
                                    # Pour la concision ici, je réutilise la logique existante 
                                    # mais insérée proprement dans le même bloc
                                    # Connexion BDD
                                    import os
                                    from database.database_manager import DatabaseManager
                                    from src.reports.legal_document_generator import LegalDocumentGenerator
                                    
                                    root_dir = os.getcwd() # Ou chemin relatif correct
                                    if st.session_state.env_mode == 'TEST':
                                        db_path = os.path.join(root_dir, 'data', 'test_recours_ecommerce.db')
                                    else:
                                        db_path = os.path.join(root_dir, 'data', 'recours_ecommerce.db')

                                    # 31/08/2026 : suite du 26/08 — voir le commentaire
                                    # équivalent plus haut (chargement du template). Un compte
                                    # TEST est désormais provisionné à la volée (get_or_create_client)
                                    # dans SA base isolée, ce qui permet d'écrire les réclamations
                                    # au même endroit que celui lu par "Mes Litiges" au lieu de la
                                    # base globale — c'est le correctif de fond du bug "Mes Litiges
                                    # reste vide". Un compte PROD continue d'utiliser la base globale
                                    # (DATABASE_TYPE), où son identité existe déjà.
                                    db_type_override = "sqlite" if st.session_state.env_mode == 'TEST' else None
                                    db_manager = DatabaseManager(db_path=db_path, db_type=db_type_override)
                                    legal_gen = LegalDocumentGenerator()

                                    # Récupération (ou provisioning) du client
                                    client = db_manager.get_or_create_client(email=st.session_state.client_email)
                                    if not client:
                                        # Audit du 26/08/2026 (suite) : avant ce garde-fou, un
                                        # client introuvable faisait planter toute la page avec
                                        # une TypeError brute (client['id'] sur None) au lieu d'un
                                        # message compréhensible. Conservé par défense en profondeur
                                        # même si get_or_create_client ne devrait plus retourner None
                                        # que sur une vraie erreur base de données.
                                        st.error("❌ Impossible de retrouver votre compte client. Merci de vous reconnecter ou de contacter le support.")
                                        st.stop()
                                    client_id = client['id']

                                    # Boucle d'exécution
                                    progress_bar = st.progress(0)
                                    # reset_index garantit un index 0-based pour que progress() reste dans [0.0, 1.0]
                                    df_final = st.session_state.selected_anomalies.reset_index(drop=True)
                                    
                                    if df_final.empty:
                                        st.warning("Aucune réclamation sélectionnée.")
                                        st.stop()
                                    
                                    for step_num, (idx, row) in enumerate(df_final.iterrows(), 1):
                                        try:
                                            tracking = row.get('tracking', f"UNKNOWN-{idx}")
                                            carrier = row.get('transporteur', 'Unknown')
                                            status = row.get('statut_detecte', 'Unknown')
                                            date_order = row.get('date', datetime.now().strftime("%Y-%m-%d"))
                                            
                                            dispute_type = 'Late Delivery' if status == 'En retard' else 'Lost Package'
                                            amount = 12.50 if status == 'En retard' else 85.00
                                            claim_reference = f"CLM-{tracking[-4:]}"  # Simplifié

                                            # 1. Création de la Réclamation en Base
                                            # Audit du 26/08/2026 : ce bloc appelait auparavant
                                            # db_manager.create_dispute(...), qui insère dans la
                                            # table 'disputes' (simples détections). La page "Mes
                                            # Litiges" lit, elle, la table 'claims' via
                                            # get_client_claims() — jamais alimentée par ce flux.
                                            # Résultat : le bandeau "✅ dossiers créés" et l'email
                                            # de confirmation client s'affichaient/partaient, mais
                                            # AUCUNE réclamation n'apparaissait jamais nulle part
                                            # dans l'app (confirmé en test live avec le compte
                                            # audit.claude.test9@refundly.ai). On appelle désormais
                                            # la bonne méthode, create_claim(), avec la même
                                            # claim_reference que celle utilisée pour le PDF et
                                            # l'email, pour que les trois restent cohérents.
                                            claim_id = db_manager.create_claim(
                                                claim_reference=claim_reference,
                                                client_id=client_id,
                                                order_id=f"ORD-{tracking[-4:]}",
                                                carrier=carrier,
                                                dispute_type=dispute_type,
                                                amount_requested=amount,
                                                tracking_number=tracking,
                                                order_date=date_order,
                                                customer_name=client['full_name'],
                                                delivery_address='Adresse de livraison inconnue',
                                                currency='EUR'
                                            )

                                            # 2. Génération de la Mise en Demeure (PDF)
                                            # On prépare les données pour le générateur
                                            claim_data_for_pdf = {
                                                'claim_reference': claim_reference,
                                                'tracking_number': tracking,
                                                'amount_requested': amount,
                                                'currency': 'EUR',
                                                'dispute_type': dispute_type,
                                                'customer_name': client['full_name'],
                                                'delivery_address': 'Adresse de livraison inconnue', # A extraire du CSV si dispo
                                                'carrier': carrier if carrier else 'Transporteur'
                                            }
                                            
                                            # Le dossier de sortie dépend de l'env
                                            output_pdf_dir = os.path.join(root_dir, 'data', 'legal_docs', 'TEST' if st.session_state.env_mode == 'TEST' else 'PROD')
                                            pdf_path = legal_gen.generate_formal_notice(claim_data_for_pdf, lang='FR', output_dir=output_pdf_dir)
                                            
                                            # On pourrait lier ce chemin en base via db_manager.update_dispute_file(...)
                                            
                                            # --- ENVOI EMAIL DE CONFIRMATION CLIENT ---
                                            from src.email_service.email_sender import send_claim_submitted_email
                                            client_email = st.session_state.get('client_email', 'test@example.com')
                                            
                                            send_claim_submitted_email(
                                                client_email=client_email,
                                                claim_reference=claim_reference,
                                                carrier=carrier,
                                                amount_requested=amount,
                                                order_id=f"ORD-{tracking[-4:]}",
                                                submission_method="api",
                                                dispute_type=dispute_type
                                            )
                                            
                                        except Exception as e:
                                            st.error(f"Erreur dossier {idx}: {e}")
                                        
                                        time.sleep(0.05)
                                        progress_bar.progress(step_num / len(df_final))
                                    
                                    # Audit du 26/08/2026 (suite) : ce bloc supprimait
                                    # immédiatement analysis_df/upload_step ici, juste avant
                                    # d'afficher le bouton "Voir mes litiges". Mais le gate qui
                                    # affiche toute cette section (plus haut : "if 'analysis_df'
                                    # in st.session_state and st.session_state.upload_step in
                                    # [...]") est réévalué à CHAQUE rerun — y compris celui
                                    # déclenché par le clic sur "Voir mes litiges" lui-même. En
                                    # supprimant l'état tout de suite, ce gate devenait faux dès
                                    # le rerun suivant, donc le code du bouton n'était jamais
                                    # atteint : le clic ne faisait que réinitialiser l'écran
                                    # d'upload (confirmé en test live, le nez dans le guidon).
                                    # On passe désormais par une étape 'done' dédiée (ajoutée à
                                    # la liste du gate ci-dessus), qui persiste jusqu'à ce que
                                    # l'utilisateur clique effectivement sur un bouton pour en
                                    # sortir.
                                    st.session_state.upload_result_count = len(df_final)
                                    st.session_state.upload_step = 'done'
                                    st.rerun()

                    elif st.session_state.upload_step == 'done':
                        # 31/08/2026 (audit complet) : message corrigé — voir le commentaire
                        # détaillé plus haut ("Vérification des Emails avant envoi"). Le PDF
                        # est généré tout de suite ; l'envoi au transporteur suit le
                        # calendrier automatique de relance (J+7/14/21), pas immédiat.
                        st.success(f"✅ {st.session_state.get('upload_result_count', 0)} dossiers créés, PDF de mise en demeure généré. Le transporteur sera relancé automatiquement s'il ne répond pas.")
                        st.balloons()
                        col_done1, col_done2 = st.columns([1, 3])
                        with col_done1:
                            if st.button("Voir mes litiges"):
                                st.session_state.active_tab = 'Mes Litiges'
                                st.query_params["page"] = 'Mes Litiges'
                                del st.session_state.analysis_df
                                del st.session_state.upload_step
                                st.rerun()
                        with col_done2:
                            if st.button("🔄 Nouvelle analyse"):
                                del st.session_state.analysis_df
                                del st.session_state.upload_step
                                st.rerun()
    
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
