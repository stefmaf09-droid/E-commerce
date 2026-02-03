"""
Tests for EmailTemplateManager - Template personnalisables.

Tests complets de la gestion des templates d'emails :
- Récupération templates (custom et default)
- Sauvegarde templates
- Suppression templates
- Rendu avec variables
"""

import pytest
import sqlite3
from src.database.email_template_manager import EmailTemplateManager


class TestEmailTemplateManager:
    """Tests du gestionnaire de templates d'emails."""
    
    @pytest.fixture
    def manager(self, tmp_path):
        """Crée un gestionnaire avec DB temporaire."""
        db_path = tmp_path / "test_templates.db"
        return EmailTemplateManager(str(db_path))
    
    def test_table_creation(self, manager):
        """Test création de la table email_templates."""
        # Vérifier que la table existe
        conn = sqlite3.connect(manager.db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='email_templates'"
        )
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None
        assert result[0] == 'email_templates'
    
    def test_get_default_template_fr(self, manager):
        """Test récupération template par défaut FR."""
        template = manager.get_template('status_request', 'FR')
        
        assert template is not None
        assert 'subject' in template
        assert 'body' in template
        assert 'Demande de mise à jour' in template['subject']
        assert '{claim_reference}' in template['subject']
        assert 'Madame, Monsieur' in template['body']
    
    def test_get_default_template_en(self, manager):
        """Test récupération template par défaut EN."""
        template = manager.get_template('warning', 'EN')
        
        assert template is not None
        assert 'Warning' in template['subject']
        assert 'Dear Sir/Madam' in template['body']
    
    def test_get_default_template_all_types(self, manager):
        """Test que tous les types de templates existent."""
        types = ['status_request', 'warning', 'formal_notice']
        
        for template_type in types:
            template = manager.get_template(template_type, 'FR')
            assert template['subject'] != ''
            assert template['body'] != ''
    
    def test_save_custom_template(self, manager):
        """Test sauvegarde d'un template personnalisé."""
        client_id = 1
        success = manager.save_template(
            client_id=client_id,
            template_type='status_request',
            language='FR',
            subject='Mon sujet personnalisé - {claim_reference}',
            body_html='<p>Mon contenu personnalisé pour {carrier}</p>'
        )
        
        assert success is True
        
        # Vérifier qu'il est bien sauvegardé
        custom_template = manager.get_template('status_request', 'FR', client_id)
        assert 'Mon sujet personnalisé' in custom_template['subject']
        assert 'Mon contenu personnalisé' in custom_template['body']
    
    def test_custom_template_overrides_default(self, manager):
        """Test qu'un template personnalisé remplace le défaut."""
        client_id = 1
        
        # Récupérer template par défaut
        default_template = manager.get_template('warning', 'FR')
        
        # Sauvegarder template personnalisé
        manager.save_template(
            client_id=client_id,
            template_type='warning',
            language='FR',
            subject='Custom Warning',
            body_html='<p>Custom body</p>'
        )
        
        # Template avec client_id doit retourner le custom
        custom_template = manager.get_template('warning', 'FR', client_id)
        assert custom_template['subject'] == 'Custom Warning'
        
        # Template sans client_id doit retourner le défaut
        default_again = manager.get_template('warning', 'FR')
        assert default_again['subject'] == default_template['subject']
    
    def test_delete_custom_template(self, manager):
        """Test suppression d'un template personnalisé."""
        client_id = 1
        
        # Sauvegarder un template
        manager.save_template(
            client_id=client_id,
            template_type='formal_notice',
            language='EN',
            subject='Custom',
            body_html='<p>Custom</p>'
        )
        
        # Vérifier qu'il existe
        custom = manager.get_template('formal_notice', 'EN', client_id)
        assert 'Custom' in custom['subject']
        
        # Supprimer
        success = manager.delete_template(client_id, 'formal_notice', 'EN')
        assert success is True
        
        # Vérifier qu'on retourne au défaut
        after_delete = manager.get_template('formal_notice', 'EN', client_id)
        assert 'Custom' not in after_delete['subject']
        assert 'FORMAL DEMAND' in after_delete['subject']  # Default EN
    
    def test_render_template_with_variables(self, manager):
        """Test rendu d'un template avec variables."""
        template = {
            'subject': 'Claim {claim_reference} - {carrier}',
            'body': '<p>Amount: {amount} {currency}</p><p>Customer: {customer_name}</p>'
        }
        
        claim_data = {
            'claim_reference': 'CLM-2026-001',
            'carrier': 'DHL',
            'amount_requested': 150.50,
            'currency': 'EUR',
            'customer_name': 'Jean Dupont',
            'tracking_number': 'DHL123',
            'delivery_address': 'Paris',
            'dispute_type': 'Lost',
            'order_id': 'ORD-123'
        }
        
        rendered = manager.render_template(template, claim_data, "Ma Société")
        
        assert rendered['subject'] == 'Claim CLM-2026-001 - DHL'
        assert '150.50' in rendered['body']
        assert 'EUR' in rendered['body']
        assert 'Jean Dupont' in rendered['body']
    
    def test_render_template_with_all_variables_provided(self, manager):
        """Test que le rendu fonctionne quand toutes les variables sont fournies."""
        template = {
            'subject': '{claim_reference}',
            'body': 'Carrier: {carrier}, Customer: {customer_name}'
        }
        
        claim_data = {
            'claim_reference': 'CLM-TEST',
            'carrier': 'DHL',
            'customer_name': 'Jean Dupont',
            'tracking_number': 'N/A',
            'amount_requested': 0,
            'currency': 'EUR',
            'delivery_address': 'N/A',
            'dispute_type': 'N/A',
            'order_id': 'N/A'
        }
        
        rendered = manager.render_template(template, claim_data)
        
        assert 'CLM-TEST' in rendered['subject']
        assert 'DHL' in rendered['body']
        assert 'Jean Dupont' in rendered['body']
    
    def test_get_all_templates(self, manager):
        """Test récupération de tous les templates d'un client."""
        client_id = 5
        
        # Créer plusieurs templates
        manager.save_template(client_id, 'status_request', 'FR', 'S1', 'B1')
        manager.save_template(client_id, 'status_request', 'EN', 'S2', 'B2')
        manager.save_template(client_id, 'warning', 'FR', 'S3', 'B3')
        
        # Récupérer tous
        all_templates = manager.get_all_templates(client_id)
        
        assert len(all_templates) == 3
        assert all(t['template_type'] in ['status_request', 'warning'] for t in all_templates)
    
    def test_update_existing_template(self, manager):
        """Test mise à jour d'un template existant."""
        client_id = 1
        
        # Créer template initial
        manager.save_template(client_id, 'warning', 'FR', 'Version 1', 'Body 1')
        
        # Mettre à jour
        manager.save_template(client_id, 'warning', 'FR', 'Version 2', 'Body 2')
        
        # Vérifier qu'il n'y a qu'un seul template (pas de doublon)
        all_templates = manager.get_all_templates(client_id)
        warning_templates = [t for t in all_templates if t['template_type'] == 'warning' and t['language'] == 'FR']
        
        assert len(warning_templates) == 1
        assert warning_templates[0]['subject'] == 'Version 2'
    
    def test_fallback_to_french_if_language_not_found(self, manager):
        """Test fallback vers FR si langue non supportée."""
        template = manager.get_template('status_request', 'ZZ')  # Langue inexistante
        
        # Doit retourner la version FR
        assert template is not None
        assert template['subject'] != ''
        assert 'Demande' in template['subject']  # FR keyword
    
    def test_available_variables_list(self, manager):
        """Test que la liste des variables disponibles est complète."""
        variables = manager.AVAILABLE_VARIABLES
        
        expected = [
            'claim_reference', 'carrier', 'tracking_number', 'amount', 'currency',
            'customer_name', 'delivery_address', 'dispute_type', 'company_name',
            'order_id', 'submission_date'
        ]
        
        for var in expected:
            assert var in variables
    
    def test_default_templates_have_all_languages(self, manager):
        """Test que tous les templates par défaut existent en FR et EN."""
        types = ['status_request', 'warning', 'formal_notice']
        languages = ['FR', 'EN']
        
        for template_type in types:
            for lang in languages:
                template = manager.get_template(template_type, lang)
                assert template['subject'] != '', f"Missing {template_type} {lang} subject"
                assert template['body'] != '', f"Missing {template_type} {lang} body"
                assert '{claim_reference}' in template['subject'], "Missing variable in subject"
                assert '{' in template['body'], "Missing variables in body"


class TestEmailTemplateManagerErrorHandling:
    """Tests de gestion d'erreurs."""
    
    def test_invalid_db_path_handled(self):
        """Test gestion d'erreurs avec chemin DB invalide."""
        manager = EmailTemplateManager("/nonexistent/path/db.db")
        
        # Ne doit pas crash, juste logger l'erreur
        assert manager is not None
    
    def test_empty_template_type(self, tmp_path):
        """Test avec type de template vide."""
        db_path = tmp_path / "test.db"
        manager = EmailTemplateManager(str(db_path))
        
        template = manager.get_template('', 'FR')
        
        # Doit retourner template vide, pas crash
        assert template == {'subject': '', 'body': ''}
    
    def test_save_with_special_characters(self, tmp_path):
        """Test sauvegarde avec caractères spéciaux."""
        db_path = tmp_path / "test.db"
        manager = EmailTemplateManager(str(db_path))
        
        success = manager.save_template(
            client_id=1,
            template_type='status_request',
            language='FR',
            subject="Réclamation №123 — 'Test' & \"Quote\"",
            body_html="<p>€ £ ¥ © ® ™</p>"
        )
        
        assert success is True
        
        template = manager.get_template('status_request', 'FR', 1)
        assert 'Réclamation' in template['subject']
        assert '€' in template['body']
