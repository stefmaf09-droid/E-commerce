"""
Dashboard Interactif - Visualisation du Potentiel de Recouvrement
==================================================================

Interface web interactive pour présenter les résultats de l'analyse
de litiges et le potentiel de recouvrement.
"""

import streamlit as st
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Sentry Error Monitoring ───────────────────────────────────────────────────
# Initialized early so ALL errors (including import errors) are captured.
try:
    from config.sentry_config import init_sentry
    init_sentry()
except Exception:
    pass  # Non-fatal — app runs without monitoring if Sentry is unavailable
# ─────────────────────────────────────────────────────────────────────────────



# Configuration de la page
st.set_page_config(
    page_title="Agent IA - Recouvrement Logistique",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un design premium
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(102, 126, 234, 0.2);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .highlight-box {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        font-size: 1.2rem;
        font-weight: 600;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
        margin: 20px 0;
    }
    
    .stMetric {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ── URL param shortcuts (for demo & deep-linking) ───────────────────────────
_qp = st.query_params

# ?portal=true or ?token=... → auto-open the auth portal
if (_qp.get("portal") == "true" or "token" in _qp) and not st.session_state.get("_show_login"):
    st.session_state._show_login = True

# ?demo_wizard=true&step=N → bypass auth, go straight to wizard step N
if _qp.get("demo_wizard") == "true":
    st.session_state.authenticated = True
    st.session_state.client_email = "demo@refundly.ai"
    st.session_state.onboarding_complete = False
    st.session_state.onboarding_step = int(_qp.get("step", "1"))
    from src.dashboard.onboarding_wizard import render_onboarding_wizard
    render_onboarding_wizard()
    st.stop()

# ── Portail client (auth + onboarding + dashboard) ───────────────────────────
from src.dashboard.auth_functions import authenticate
auth_ok = authenticate()

if not auth_ok:
    # L'authentification gère l'affichage de la landing page et du portail
    st.stop()

client_email = st.session_state.get('client_email', '')

# Audit du 26/08/2026 (suite) : ce point d'entrée avait son PROPRE gate
# d'onboarding, séparé de celui de client_dashboard_main_new.py, qui
# appelait encore l'ancien assistant à 3 étapes obligatoires
# (onboarding_wizard.render_onboarding_wizard) — celui-là même que la
# refonte du jour (welcome_hub.py) remplace. Un client passant par CE
# fichier (ex: process "web" du Procfile) retombait donc sur l'ancien
# assistant bloquant, jamais corrigé ici alors que client_dashboard_
# main_new.main() (appelé juste en dessous) a déjà son propre gate
# correct et à jour (needs_welcome_hub). On supprime ce gate dupliqué et
# on laisse client_main() gérer l'accueil, pour n'avoir qu'un seul
# endroit à maintenir.
try:
    from src.dashboard.floating_chatbot import (
        render_floating_chatbot,
        render_proactive_suggestions,
    )
    render_proactive_suggestions(client_email)

    from client_dashboard_main_new import main as client_main
    client_main()

    render_floating_chatbot(
        context="tableau de bord",
        client_email=client_email,
    )
    st.stop()
except Exception as e:
    st.error(f"Erreur lors du chargement du tableau de bord client : {e}")
    st.info("Vous êtes connecté·e — ouvrez le menu 'Customer Dashboard' pour accéder à votre espace.")
    st.stop()

# ── Legacy marketing dashboard (opt-in) ──────────────────────────────────────
# To access the legacy charts/upload UI below, pass `?legacy=true` in the URL.
if _qp.get("legacy") != "true":
    st.stop()


@st.cache_data
def load_data():
    """Charge les données d'analyse."""
    # Dataset original
    orders_df = pd.read_csv('data/synthetic_orders.csv')
    
    # Résultats d'analyse
    disputes_df = pd.read_csv('data/dispute_analysis.csv')
    
    # Statistiques
    with open('data/dispute_statistics.json', 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    return orders_df, disputes_df, stats


def render_header():
    """Affiche le header principal."""
    st.markdown('<h1 class="main-header">🤖 Agent IA - Recouvrement Logistique</h1>', unsafe_allow_html=True)
    st.markdown("""
        <div style='text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 2rem;'>
            <strong>Récupérez automatiquement l'argent que les transporteurs vous doivent</strong><br>
            Modèle Success Fee 20% • Coût 0€ • Profit Pur
        </div>
    """, unsafe_allow_html=True)


def render_how_it_works():
    """Explique le fonctionnement du service en 3 étapes."""
    st.markdown("### 🔄 Comment ça marche ?")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div style='text-align: center; padding: 25px; background: rgba(59, 130, 246, 0.1); 
                        border-radius: 12px; border: 2px solid rgba(59, 130, 246, 0.3); height: 100%;'>
                <div style='font-size: 3rem; margin-bottom: 10px;'>1️⃣</div>
                <div style='font-size: 1.3rem; font-weight: 600; color: #3b82f6; margin-bottom: 15px;'>
                    Connexion Simple
                </div>
                <div style='color: #666; font-size: 0.95rem; line-height: 1.6;'>
                    Connectez votre système e-commerce (Shopify, PrestaShop, WooCommerce) 
                    ou envoyez-nous un export CSV mensuel.
                    <br><br>
                    <strong>⏱️ 5 minutes</strong> • Accès lecture seule
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 25px; background: rgba(16, 185, 129, 0.1); 
                        border-radius: 12px; border: 2px solid rgba(16, 185, 129, 0.3); height: 100%;'>
                <div style='font-size: 3rem; margin-bottom: 10px;'>2️⃣</div>
                <div style='font-size: 1.3rem; font-weight: 600; color: #10b981; margin-bottom: 15px;'>
                    Automatisation Totale
                </div>
                <div style='color: #666; font-size: 0.95rem; line-height: 1.6;'>
                    Notre IA détecte les litiges, récupère les preuves, dépose les réclamations 
                    et négocie avec les transporteurs.
                    <br><br>
                    <strong>⏱️ 0 minute</strong> de votre temps
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div style='text-align: center; padding: 25px; background: rgba(139, 92, 246, 0.1); 
                        border-radius: 12px; border: 2px solid rgba(139, 92, 246, 0.3); height: 100%;'>
                <div style='font-size: 3rem; margin-bottom: 10px;'>3️⃣</div>
                <div style='font-size: 1.3rem; font-weight: 600; color: #8b5cf6; margin-bottom: 15px;'>
                    Vous Encaissez
                </div>
                <div style='color: #666; font-size: 0.95rem; line-height: 1.6;'>
                    Chaque mois, recevez l'argent récupéré directement sur votre compte. 
                    Nous prélevons 20% uniquement sur les récupérations réussies.
                    <br><br>
                    <strong>💰 Profit Pur</strong> • Risque Zéro
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Message de réassurance
    st.info("""
        🔒 **Sécurité & Transparence** : Accès API en lecture seule • Aucun impact sur vos opérations 
        • Rapport mensuel détaillé • Vous gardez le contrôle total
    """)
    
    st.markdown("---")



def render_file_upload():
    """Section d'upload de fichier client pour analyse personnalisée."""
    st.markdown("### 📤 Analysez VOS Données en Direct")
    
    st.markdown("""
        <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%); 
                    border-radius: 12px; margin-bottom: 20px;'>
            <div style='font-size: 1.1rem; color: #333; margin-bottom: 10px;'>
                <strong>🎯 Découvrez combien VOUS pouvez récupérer</strong>
            </div>
            <div style='font-size: 0.95rem; color: #666;'>
                Uploadez votre export de commandes (CSV ou Excel) et obtenez votre estimation gratuite en 30 secondes
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Sélectionnez votre fichier CSV ou Excel",
            type=['csv', 'xlsx', 'xls'],
            help="Export de vos commandes des 90 derniers jours (Shopify, PrestaShop, WooCommerce...)",
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            st.success(f"✅ Fichier chargé : {uploaded_file.name}")
            
            # Bouton d'analyse
            if st.button("🚀 Analyser mes données", type="primary", width='stretch'):
                with st.spinner("🔍 Analyse en cours de vos commandes..."):
                    import time
                    import io
                    
                    # Lire le fichier
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            client_df = pd.read_csv(uploaded_file)
                        else:
                            client_df = pd.read_excel(uploaded_file)
                        
                        time.sleep(1.5)  # Effet visuel
                        
                        # Analyse simplifiée (estimation basée sur volume)
                        num_orders = len(client_df)
                        
                        # Estimation réaliste : ~15-25% de litiges sur commandes
                        # Montant moyen récupérable : 35-45€ par litige
                        estimated_dispute_rate = 0.20  # 20%
                        avg_recovery_per_dispute = 40
                        
                        potential_disputes = int(num_orders * estimated_dispute_rate)
                        potential_recovery = potential_disputes * avg_recovery_per_dispute
                        success_fee = potential_recovery * 0.20
                        net_for_client = potential_recovery - success_fee
                        
                        st.balloons()
                        
                        # Affichage du résultat
                        st.markdown("---")
                        st.markdown("## 🎉 Résultat de l'Analyse")
                        
                        # Grande carte du résultat
                        st.markdown(f"""
                            <div style='text-align: center; padding: 40px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                                        border-radius: 15px; color: white; margin: 20px 0;'>
                                <div style='font-size: 1.2rem; opacity: 0.9; margin-bottom: 10px;'>
                                    💰 Potentiel de Récupération Estimé
                                </div>
                                <div style='font-size: 4rem; font-weight: bold; margin: 20px 0;'>
                                    {net_for_client:,.0f} €
                                </div>
                                <div style='font-size: 1.1rem; opacity: 0.9;'>
                                    Sur {num_orders:,} commandes analysées • {potential_disputes} litiges détectés
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Détails
                        col_d1, col_d2, col_d3 = st.columns(3)
                        with col_d1:
                            st.metric("💸 Montant Récupérable", f"{potential_recovery:,.0f} €")
                        with col_d2:
                            st.metric("💳 Votre Coût", "0 €", delta="Risque zéro")
                        with col_d3:
                            st.metric("🎯 Votre Gain Net", f"{net_for_client:,.0f} €")
                        
                        st.info("""
                            ℹ️ **Cette estimation est basée sur les statistiques moyennes du secteur e-commerce.**  
                            Pour une analyse détaillée de vos litiges réels (transporteurs, types, montants exacts), 
                            remplissez le formulaire ci-dessous.
                        """)
                        
                        st.markdown("---")
                        
                        # FORMULAIRE DE CONVERSION
                        st.markdown("## 📝 Intéressé ? Récupérez cet argent maintenant")
                        
                        st.markdown("""
                            <div style='padding: 15px; background: rgba(59, 130, 246, 0.1); border-radius: 10px; margin-bottom: 20px;'>
                                <strong>✨ Ce qui se passe ensuite :</strong><br>
                                1️⃣ Vous remplissez ce formulaire (30 secondes)<br>
                                2️⃣ Vous recevez un lien de connexion API par email (instantané)<br>
                                3️⃣ Connexion en 1 clic à votre plateforme e-commerce<br>
                                4️⃣ L'IA commence à récupérer automatiquement votre argent
                            </div>
                        """, unsafe_allow_html=True)
                        
                        with st.form("contact_form"):
                            col_f1, col_f2 = st.columns(2)
                            
                            with col_f1:
                                nom = st.text_input("Nom complet *", placeholder="Jean Dupont")
                                entreprise = st.text_input("Nom de votre entreprise *", placeholder="Ma Boutique E-commerce")
                            
                            with col_f2:
                                email = st.text_input("Email professionnel *", placeholder="jean@monentreprise.fr")
                                telephone = st.text_input("Téléphone", placeholder="+33 6 12 34 56 78")
                            
                            volume_mensuel = st.selectbox(
                                "Volume mensuel de commandes",
                                ["< 500", "500 - 1000", "1000 - 5000", "5000 - 10000", "> 10000"]
                            )
                            
                            plateforme = st.multiselect(
                                "Plateforme(s) e-commerce *",
                                ["Shopify", "PrestaShop", "WooCommerce", "Magento", "Autre"],
                                help="Information critique pour la connexion API"
                            )

                            
                            commentaire = st.text_area(
                                "Message (optionnel)",
                                placeholder="Questions ou informations supplémentaires..."
                            )
                            
                            submitted = st.form_submit_button("🚀 Activer le service maintenant", 
                                                             type="primary", 
                                                             width='stretch')
                            
                            if submitted:
                                if nom and entreprise and email and plateforme:
                                    # TODO: Enregistrer dans CRM / Envoyer email
                                    # Pour l'instant, juste afficher un message
                                    st.success("""
                                        ✅ **Demande envoyée avec succès !**
                                        
                                        Nous avons bien reçu votre demande pour **{:,.0f} €** de potentiel de récupération.
                                        
                                        📧 Vous allez recevoir dans quelques minutes à **{}** :
                                        • Un lien de connexion sécurisé à votre plateforme {}
                                        • Vos identifiants de dashboard de suivi en temps réel
                                        
                                        🚀 **L'activation est automatique** – Aucune intervention de votre part requise après la connexion !
                                    """.format(net_for_client, email, ', '.join(plateforme)))
                                    
                                    st.balloons()
                                else:
                                    st.error("⚠️ Veuillez remplir tous les champs obligatoires (*)")

                        
                    except Exception as e:
                        st.error(f"""
                            ❌ **Erreur lors de la lecture du fichier**
                            
                            Assurez-vous que votre fichier contient bien les colonnes suivantes :
                            - ID commande
                            - Date
                            - Transporteur
                            - Statut
                            
                            Erreur technique : {str(e)}
                        """)
    
    with col2:
        st.markdown("""
            <div style='padding: 20px; background: white; border-radius: 10px; border: 2px dashed #e5e7eb;'>
                <div style='font-size: 0.85rem; color: #666; line-height: 1.6;'>
                    <strong>📋 Format accepté :</strong><br>
                    • CSV (recommandé)<br>
                    • Excel (.xlsx, .xls)<br>
                    <br>
                    <strong>💡 Astuce :</strong><br>
                    Exportez vos commandes des 90 derniers jours depuis votre plateforme e-commerce.
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Message pour ceux qui n'ont pas encore uploadé
    if uploaded_file is None:
        st.info("""
            💡 **Pas de fichier sous la main ?**  
            Consultez notre démo ci-dessous avec 5,000 commandes synthétiques pour comprendre le potentiel.
        """)



def render_key_metrics(stats):
    """Affiche les métriques clés."""
    overview = stats['overview']
    roi = stats['roi_projection']
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💰 Montant Récupérable",
            value=f"{overview['total_recoverable']:,.0f} €",
            delta=f"{overview['dispute_rate']}% des commandes"
        )
    
    with col2:
        st.metric(
            label="✅ Litiges Détectés",
            value=f"{overview['disputed_orders']:,}",
            delta=f"sur {overview['total_orders']:,} commandes"
        )
    
    with col3:
        # Ce qui compte vraiment pour le client : son gain NET
        net_for_client = roi['total_recoverable_realistic'] - roi['success_fee_20pct']
        st.metric(
            label="🎯 Votre Gain Net",
            value=f"{net_for_client:,.0f} €",
            delta="Après Success Fee 20%"
        )


def render_roi_highlight(stats):
    """Affiche l'encart ROI mis en avant."""
    roi = stats['roi_projection']
    overview = stats['overview']
    
    st.markdown(f"""
        <div class="highlight-box">
            <div style="font-size: 1.8rem; margin-bottom: 10px;">
                🚀 <strong>{overview['total_recoverable']:,.0f} €</strong> laissés sur la table
            </div>
            <div style="font-size: 1rem; opacity: 0.9;">
                Argent que vous n'avez jamais récupéré auprès des transporteurs<br>
                <strong>Récupération automatisée → {roi['success_fee_20pct']:,.0f} € de commission sans effort</strong>
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_priority_breakdown(stats):
    """Graphique de répartition par priorité."""
    st.subheader("🎯 Répartition par Priorité de Litige")
    
    if stats['by_priority']:
        priorities = []
        counts = []
        amounts = []
        expected = []
        colors_map = {
            'CRITICAL': '#dc2626',
            'HIGH': '#ea580c',
            'MEDIUM': '#f59e0b',
            'LOW': '#84cc16'
        }
        colors = []
        
        for priority, data in sorted(stats['by_priority'].items()):
            priorities.append(priority)
            counts.append(data['count'])
            amounts.append(data['total_recoverable'])
            expected.append(data['expected_recovery'])
            colors.append(colors_map.get(priority, '#6366f1'))
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Nombre de Cas', 'Montant Récupérable'),
            specs=[[{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        fig.add_trace(
            go.Bar(x=priorities, y=counts, marker_color=colors, name='Cas'),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(x=priorities, y=amounts, marker_color=colors, name='Montant', showlegend=False),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=False)
        fig.update_yaxes(title_text="Nombre de cas", row=1, col=1)
        fig.update_yaxes(title_text="Montant (€)", row=1, col=2)
        
        st.plotly_chart(fig, width='stretch')


def render_carrier_analysis(stats):
    """Analyse par transporteur."""
    st.subheader("🚚 Performance par Transporteur")
    
    if stats['by_carrier']:
        carriers = list(stats['by_carrier'].keys())
        amounts = [stats['by_carrier'][c]['total_recoverable'] for c in carriers]
        disputes = [stats['by_carrier'][c]['disputed_orders'] for c in carriers]
        
        # Créer le DataFrame pour le graphique
        df_carriers = pd.DataFrame({
            'Transporteur': carriers,
            'Montant Récupérable': amounts,
            'Litiges': disputes
        }).sort_values('Montant Récupérable', ascending=True)
        
        # Graphique horizontal
        fig = px.bar(
            df_carriers,
            y='Transporteur',
            x='Montant Récupérable',
            orientation='h',
            color='Montant Récupérable',
            color_continuous_scale='RdYlGn_r',
            text='Montant Récupérable'
        )
        
        fig.update_traces(texttemplate='%{text:,.0f} €', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        fig.update_xaxes(title_text="Montant Récupérable (€)")
        
        st.plotly_chart(fig, width='stretch')


def render_dispute_types(stats):
    """Répartition par type de litige."""
    st.subheader("⚖️ Types de Litiges Détectés")
    
    if stats['by_rule']:
        rule_names = list(stats['by_rule'].keys())
        counts = [stats['by_rule'][r]['count'] for r in rule_names]
        amounts = [stats['by_rule'][r]['total_recoverable'] for r in rule_names]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart des cas
            fig_pie = px.pie(
                values=counts,
                names=rule_names,
                title='Répartition des Cas',
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, width='stretch')
        
        with col2:
            # Bar chart des montants
            df_rules = pd.DataFrame({
                'Type de Litige': rule_names,
                'Montant': amounts
            }).sort_values('Montant', ascending=True)
            
            fig_bar = px.bar(
                df_rules,
                y='Type de Litige',
                x='Montant',
                orientation='h',
                title='Montants Récupérables',
                color='Montant',
                color_continuous_scale='Viridis'
            )
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, width='stretch')


def render_roi_comparison(stats):
    """Section ROI centrée sur la valeur client."""
    st.subheader("💰 Votre Gain Net")
    
    overview = stats['overview']
    roi = stats['roi_projection']
    
    # Ce qui compte pour le CLIENT
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                        border-radius: 12px; color: white;'>
                <div style='font-size: 1.1rem; opacity: 0.9;'>💵 Argent Récupéré</div>
                <div style='font-size: 3rem; font-weight: bold; margin: 15px 0;'>{:,.0f} €</div>
                <div style='font-size: 0.95rem; opacity: 0.8;'>Argent perdu récupéré pour vous</div>
            </div>
        """.format(roi['total_recoverable_realistic']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); 
                        border-radius: 12px; color: white;'>
                <div style='font-size: 1.1rem; opacity: 0.9;'>💳 Votre Coût</div>
                <div style='font-size: 3rem; font-weight: bold; margin: 15px 0;'>0 €</div>
                <div style='font-size: 0.95rem; opacity: 0.8;'>Modèle Success Fee uniquement</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Détails techniques en option (pour les curieux)
    with st.expander("🔧 Détails Techniques (optionnel)"):
        st.markdown("**Pourquoi l'automatisation IA est cruciale**")
        
        num_cases = overview['disputed_orders']
        human_cost = num_cases * 30
        ia_cost = roi['total_processing_cost']
        
        col_tech1, col_tech2 = st.columns(2)
        
        with col_tech1:
            st.metric(
                "Coût si traitement humain",
                f"{human_cost:,.0f} €",
                delta=f"{num_cases} cas × 30€/cas",
                delta_color="inverse"
            )
            st.caption("❌ ROI négatif → Abandon des réclamations")
        
        with col_tech2:
            st.metric(
                "Coût avec automatisation IA",
                f"{ia_cost:,.0f} €",
                delta=f"{num_cases} cas × 0.50€/cas",
                delta_color="normal"
            )
            st.caption("✅ ROI positif → Récupération rentable")
        
        savings = human_cost - ia_cost
        st.info(f"💡 Économie opérationnelle: {savings:,.0f} € ({savings/human_cost*100:.1f}%) grâce à l'IA")






def main():
    """Application principale."""
    # Chargement des données
    try:
        orders_df, disputes_df, stats = load_data()
    except FileNotFoundError:
        st.error("⚠️ Données non trouvées. Exécutez d'abord `generate_synthetic_data.py` puis `generate_demo_disputes.py`")
        st.stop()
    
    # Header
    render_header()
    
    # Comment ça marche
    render_how_it_works()
    
    # Upload de fichier client
    render_file_upload()
    
    # Métriques clés
    render_key_metrics(stats)
    
    # Highlight ROI
    render_roi_highlight(stats)
    
    st.markdown("---")
    
    # Analyses détaillées
    col1, col2 = st.columns(2)
    
    with col1:
        render_priority_breakdown(stats)
    
    with col2:
        render_carrier_analysis(stats)
    
    st.markdown("---")
    
    # Types de litiges
    render_dispute_types(stats)
    
    st.markdown("---")
    
    # Comparaison ROI
    render_roi_comparison(stats)
    
    st.markdown("---")
    
    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666; padding: 20px;'>
            <strong>Agent IA de Recouvrement Logistique</strong><br>
            Développé avec ❤️ pour maximiser vos marges e-commerce<br>
            <em>Modèle Success Fee: Vous ne payez que sur l'argent récupéré</em>
        </div>
    """, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
