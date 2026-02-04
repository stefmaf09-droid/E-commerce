"""
Database Manager - Gestionnaire centralisé pour toutes les opérations de base de données.

Gère:
- Connexions SQLite/PostgreSQL
- CRUD pour toutes les tables
- Transactions
- Migrations
"""

import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
import json
import logging
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2 import extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire centralisé de base de données."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize database manager.
        
        Args:
            db_path: Chemin vers la base SQLite. Si None, utilise database/main.db
        """
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'main.db')
        
        self.db_path = db_path
        self.db_type = os.getenv('DATABASE_TYPE', 'sqlite').lower()
        self.pg_url = os.getenv('DATABASE_URL')
        
        # Caractère de substitution (placeholder) pour SQL
        self.placeholder = '?' if self.db_type == 'sqlite' else '%s'
        
        if self.db_type == 'sqlite':
            self._ensure_database_exists()
        else:
            logger.info("Using PostgreSQL Backend (Supabase/Neon)")
    
    def _ensure_database_exists(self):
        """Créer la base et les tables si elles n'existent pas."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Vérification plus robuste : est-ce que les tables existent ?
        conn = self.get_connection()
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                logger.info(f"Initializing schema for {self.db_path}")
                # Créer tables depuis schema.sql
                # On remonte de 2 niveaux (src/database) -> racine -> database -> schema.sql ??
                # Attention au chemin relatif selon ou est lancé le script
                
                # Tentative 1: Chemin relatif standard projet
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                schema_path = os.path.join(base_dir, 'database', 'schema.sql')
                
                if not os.path.exists(schema_path):
                     # Fallback pour le run local d:\Recours_Ecommerce
                     schema_path = os.path.join(base_dir, 'schema.sql')

                if os.path.exists(schema_path):
                    with open(schema_path, 'r', encoding='utf-8') as f:
                        schema = f.read()
                    conn.executescript(schema)
                    conn.commit()
                    
                    # Si c'est la base de test, on injecte un client admin par défaut pour éviter le crash
                    if 'test' in self.db_path.lower():
                        conn.execute("INSERT OR IGNORE INTO clients (email, full_name) VALUES ('admin@refundly.ai', 'Admin Test')")
                        conn.commit()
                        
                    logger.info(f"Database initialized successfully at {self.db_path}")
                else:
                    logger.error(f"Schema file not found at {schema_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            # Ne pas raise ici pour laisser une chance, mais c'est critique
        finally:
            conn.close()
    
    def get_connection(self):
        """Obtenir une connexion à la base de données (SQLite ou Postgres)."""
        if self.db_type == 'sqlite':
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL support")
            
            try:
                # Robust parsing of the DATABASE_URL
                if not self.pg_url:
                    raise ValueError("DATABASE_URL non configuré dans les Secrets.")
                
                result = urlparse(self.pg_url)
                username = result.username
                password = result.password
                database = result.path[1:]
                hostname = result.hostname
                port = result.port or 5432
                
                import urllib.parse
                import socket
                if password:
                    password = urllib.parse.unquote(password)
                
                # FORCE IPv4 : Streamlit Cloud a parfois du mal avec l'IPv6 de Supabase
                # ("Cannot assign requested address")
                try:
                    ipv4_hostname = socket.gethostbyname(hostname)
                    logger.info(f"Resolved {hostname} to IPv4: {ipv4_hostname}")
                    hostname = ipv4_hostname
                except Exception as e:
                    logger.warning(f"Could not force IPv4 for {hostname}: {e}")

                conn = psycopg2.connect(
                    host=hostname,
                    database=database,
                    user=username,
                    password=password,
                    port=port,
                    sslmode='require',
                    connect_timeout=15
                )
                return conn
            except Exception as e:
                logger.error(f"PostgreSQL connection failed: {e}")
                raise ConnectionError(f"Erreur de connexion Cloud (IPv4 Forcé) : {str(e)}")


    def _execute(self, conn, query: str, params: tuple = ()):
        """Exécute une requête en adaptant les placeholders."""
        if self.db_type == 'postgres':
            query = query.replace('?', '%s')
            cursor = conn.cursor(cursor_factory=extras.DictCursor)
        else:
            cursor = conn.cursor()
        
        cursor.execute(query, params)
        return cursor

    
    # ========================================
    # CLIENTS
    # ========================================
    
    def create_client(self, email: str, full_name: str = None, 
                     company_name: str = None, phone: str = None) -> int:
        """Créer un nouveau client."""
        conn = self.get_connection()
        try:
            query = "INSERT INTO clients (email, full_name, company_name, phone) VALUES (?, ?, ?, ?)"
            if self.db_type == 'postgres':
                query += " RETURNING id"
            
            cursor = self._execute(conn, query, (email, full_name, company_name, phone))
            
            if self.db_type == 'postgres':
                new_id = cursor.fetchone()[0]
            else:
                new_id = cursor.lastrowid
                
            conn.commit()
            logger.info(f"Client created: {email}")
            return new_id
        except Exception as e:
            # Check for unique constraint manually to avoid DB differences
            logger.warning(f"Client creation failed or exists: {email} - {e}")
            cursor = self._execute(conn, "SELECT id FROM clients WHERE email = ?", (email,))
            row = cursor.fetchone()
            return row[0] if row else None
        finally:
            conn.close()
    
    def get_client(self, email: str = None, client_id: int = None) -> Optional[Dict[str, Any]]:
        """Récupérer un client par email ou ID."""
        conn = self.get_connection()
        try:
            if email:
                cursor = self._execute(conn, "SELECT * FROM clients WHERE email = ?", (email,))
            elif client_id:
                cursor = self._execute(conn, "SELECT * FROM clients WHERE id = ?", (client_id,))
            else:
                raise ValueError("email or client_id required")
            
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def update_client(self, client_id: int, **kwargs):
        """Mettre à jour un client."""
        valid_fields = [
            'full_name', 'company_name', 'phone', 'is_active', 
            'stripe_account_id', 'stripe_onboarding_completed',
            'stripe_connect_id', 'stripe_onboarding_status',
            'subscription_tier', 'commission_rate'
        ]
        
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        if not updates:
            return
        
        updates['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [client_id]
        
        conn = self.get_connection()
        try:
            self._execute(conn, f"UPDATE clients SET {set_clause} WHERE id = ?", tuple(values))
            conn.commit()
            logger.info(f"Client {client_id} updated")
        finally:
            conn.close()
    
    # ========================================
    # CLAIMS (Réclamations)
    # ========================================
    
    def create_claim(self, claim_reference: str, client_id: int, 
                    order_id: str, carrier: str, dispute_type: str,
                    amount_requested: float, **kwargs) -> int:
        """Créer une nouvelle réclamation."""
        conn = self.get_connection()
        try:
            store_id = kwargs.get('store_id')
            tracking_number = kwargs.get('tracking_number')
            order_date = kwargs.get('order_date')
            customer_name = kwargs.get('customer_name')
            delivery_address = kwargs.get('delivery_address')
            currency = kwargs.get('currency', 'EUR')
            
            query = """
                INSERT INTO claims (
                    claim_reference, client_id, store_id, order_id, carrier,
                    dispute_type, amount_requested, tracking_number, order_date,
                    customer_name, delivery_address, currency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if self.db_type == 'postgres':
                query += " RETURNING id"
                
            cursor = self._execute(conn, query, (
                claim_reference, client_id, store_id, order_id, carrier,
                dispute_type, amount_requested, tracking_number, order_date,
                customer_name, delivery_address, currency
            ))
            
            new_id = cursor.fetchone()[0] if self.db_type == 'postgres' else cursor.lastrowid
            conn.commit()
            logger.info(f"Claim created: {claim_reference}")
            return new_id
        finally:
            conn.close()
    
    def get_claim(self, claim_reference: str = None, claim_id: int = None) -> Optional[Dict[str, Any]]:
        """Récupérer une réclamation."""
        conn = self.get_connection()
        try:
            if claim_reference:
                cursor = self._execute(conn, "SELECT * FROM claims WHERE claim_reference = ?", (claim_reference,))
            elif claim_id:
                cursor = self._execute(conn, "SELECT * FROM claims WHERE id = ?", (claim_id,))
            else:
                raise ValueError("claim_reference or claim_id required")
            
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def update_claim(self, claim_id: int, **kwargs):
        """Mettre à jour une réclamation."""
        valid_fields = [
            'status', 'submitted_at', 'response_deadline', 'response_received_at',
            'accepted_amount', 'rejection_reason', 'payment_status', 'payment_date',
            'skill_used', 'automation_status', 'automation_error',
            'evidence_uploaded', 'evidence_count',
            'follow_up_level', 'last_follow_up_at'
        ]
        
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        if not updates:
            return
        
        updates['updated_at'] = datetime.now()
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [claim_id]
        
        conn = self.get_connection()
        try:
            self._execute(conn, f"UPDATE claims SET {set_clause} WHERE id = ?", tuple(values))
            conn.commit()
            logger.info(f"Claim {claim_id} updated")
        finally:
            conn.close()
    
    def get_client_claims(self, client_id: int, status: str = None) -> List[Dict[str, Any]]:
        """Récupérer toutes les réclamations d'un client."""
        conn = self.get_connection()
        try:
            if status:
                query = "SELECT * FROM claims WHERE client_id = ? AND status = ? ORDER BY created_at DESC"
                cursor = self._execute(conn, query, (client_id, status))
            else:
                query = "SELECT * FROM claims WHERE client_id = ? ORDER BY created_at DESC"
                cursor = self._execute(conn, query, (client_id,))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    # ========================================
    # DISPUTES (Détections)
    # ========================================
    
    def create_dispute(self, client_id: int, order_id: str, carrier: str,
                      dispute_type: str, amount_recoverable: float, **kwargs) -> int:
        """Créer une détection de litige."""
        conn = self.get_connection()
        try:
            store_id = kwargs.get('store_id')
            order_date = kwargs.get('order_date')
            expected_delivery_date = kwargs.get('expected_delivery_date')
            actual_delivery_date = kwargs.get('actual_delivery_date')
            tracking_number = kwargs.get('tracking_number')
            customer_name = kwargs.get('customer_name')
            currency = kwargs.get('currency', 'EUR')
            success_probability = kwargs.get('success_probability')
            predicted_days = kwargs.get('predicted_days_to_recovery')
            
            query = """
                INSERT INTO disputes (
                    client_id, store_id, order_id, carrier, dispute_type,
                    amount_recoverable, order_date, expected_delivery_date,
                    actual_delivery_date, tracking_number, customer_name, currency,
                    success_probability, predicted_days_to_recovery
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            if self.db_type == 'postgres':
                query += " RETURNING id"
                
            cursor = self._execute(conn, query, (
                client_id, store_id, order_id, carrier, dispute_type,
                amount_recoverable, order_date, expected_delivery_date,
                actual_delivery_date, tracking_number, customer_name, currency,
                success_probability, predicted_days
            ))
            
            new_id = cursor.fetchone()[0] if self.db_type == 'postgres' else cursor.lastrowid
            conn.commit()
            logger.info(f"Dispute created for client {client_id}: {order_id}")
            return new_id
        finally:
            conn.close()
    
    def get_client_disputes(self, client_id: int, is_claimed: bool = None) -> List[Dict[str, Any]]:
        """Récupérer les litiges d'un client."""
        conn = self.get_connection()
        try:
            if is_claimed is not None:
                query = "SELECT * FROM disputes WHERE client_id = ? AND is_claimed = ? ORDER BY detected_at DESC"
                cursor = self._execute(conn, query, (client_id, 1 if is_claimed else 0))
            else:
                query = "SELECT * FROM disputes WHERE client_id = ? ORDER BY detected_at DESC"
                cursor = self._execute(conn, query, (client_id,))
            
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
    
    def mark_dispute_claimed(self, dispute_id: int, claim_id: int):
        """Marquer un litige comme réclamé."""
        conn = self.get_connection()
        try:
            self._execute(conn, "UPDATE disputes SET is_claimed = 1, claim_id = ? WHERE id = ?", (claim_id, dispute_id))
            conn.commit()
            logger.info(f"Dispute {dispute_id} marked as claimed")
        finally:
            conn.close()
    
    # ========================================
    # PAYMENTS
    # ========================================
    
    def create_payment(self, claim_id: int, client_id: int, total_amount: float,
                      client_share: float, platform_fee: float, 
                      payment_method: str = 'manual_transfer') -> int:
        """Créer un enregistrement de paiement."""
        conn = self.get_connection()
        try:
            query = """
                INSERT INTO payments (
                    claim_id, client_id, total_amount, client_share,
                    platform_fee, payment_method
                ) VALUES (?, ?, ?, ?, ?, ?)
            """
            if self.db_type == 'postgres':
                query += " RETURNING id"
                
            cursor = self._execute(conn, query, (claim_id, client_id, total_amount, client_share, platform_fee, payment_method))
            
            new_id = cursor.fetchone()[0] if self.db_type == 'postgres' else cursor.lastrowid
            conn.commit()
            logger.info(f"Payment created for claim {claim_id}")
            return new_id
        finally:
            conn.close()
    
    def update_payment(self, payment_id: int, **kwargs):
        """Mettre à jour un paiement."""
        valid_fields = ['payment_status', 'transaction_reference', 
                       'stripe_transfer_id', 'paid_at', 'notes']
        
        updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        if not updates:
            return
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [payment_id]
        
        conn = self.get_connection()
        try:
            self._execute(conn, f"UPDATE payments SET {set_clause} WHERE id = ?", tuple(values))
            conn.commit()
            logger.info(f"Payment {payment_id} updated")
        finally:
            conn.close()
    
    # ========================================
    # NOTIFICATIONS
    # ========================================
    
    def log_notification(self, client_id: int, notification_type: str,
                        subject: str, sent_to: str, status: str = 'sent',
                        related_claim_id: int = None, error_message: str = None) -> int:
        """Logger un email envoyé."""
        conn = self.get_connection()
        try:
            query = """
                INSERT INTO notifications (
                    client_id, notification_type, subject, sent_to,
                    status, related_claim_id, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            if self.db_type == 'postgres':
                query += " RETURNING id"
                
            cursor = self._execute(conn, query, (client_id, notification_type, subject, sent_to, status, related_claim_id, error_message))
            
            new_id = cursor.fetchone()[0] if self.db_type == 'postgres' else cursor.lastrowid
            conn.commit()
            return new_id
        finally:
            conn.close()
    
    # ========================================
    # ACTIVITY LOGS
    # ========================================
    
    def log_activity(self, action: str, client_id: int = None,
                    resource_type: str = None, resource_id: int = None,
                    details: Dict[str, Any] = None, ip_address: str = None,
                    user_agent: str = None):
        """Logger une activité (pour audit et RGPD)."""
        conn = self.get_connection()
        try:
            details_json = json.dumps(details) if details else None
            
            self._execute(conn, """
                INSERT INTO activity_logs (
                    client_id, action, resource_type, resource_id,
                    details, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (client_id, action, resource_type, resource_id, details_json, ip_address, user_agent))
            
            conn.commit()
        finally:
            conn.close()
    
    # ========================================
    # STATISTICS
    # ========================================
    
    def get_client_statistics(self, client_id: int) -> Dict[str, Any]:
        """Récupérer les statistiques d'un client."""
        conn = self.get_connection()
        try:
            cursor = self._execute(conn, "SELECT * FROM client_statistics WHERE client_id = ?", (client_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()
    
    def get_all_statistics(self) -> List[Dict[str, Any]]:
        """Récupérer les statistiques de tous les clients (admin)."""
        conn = self.get_connection()
        try:
            cursor = self._execute(conn, "SELECT * FROM client_statistics")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()


# Instance globale
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Obtenir l'instance globale du gestionnaire de BDD."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
