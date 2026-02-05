-- ================================================
-- Base de données Production - Recours E-commerce
-- ================================================
-- Table: Clients
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    stripe_account_id TEXT UNIQUE,
    stripe_onboarding_completed BOOLEAN DEFAULT 0,
    stripe_connect_id TEXT UNIQUE,
    -- ID Stripe Connect (acct_...)
    stripe_onboarding_status TEXT DEFAULT 'pending',
    -- pending, restricted, active
    subscription_tier TEXT DEFAULT 'standard',
    -- standard, business, enterprise
    commission_rate REAL DEFAULT 20.0,
    -- Pourcentage de commission (Success Fee)
    notification_preferences TEXT -- JSON: {claim_created, claim_updated, payment_received, frequency}
);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_stripe ON clients(stripe_account_id);
-- Table: Stores (Multi-store support)
CREATE TABLE IF NOT EXISTS stores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    -- shopify, woocommerce, etc.
    store_name TEXT NOT NULL,
    store_url TEXT,
    country TEXT DEFAULT 'FR',
    -- FR, US, UK, etc.
    currency TEXT DEFAULT 'EUR',
    -- EUR, USD, GBP, etc.
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_stores_client ON stores(client_id);
-- Table: Claims (Réclamations)
CREATE TABLE IF NOT EXISTS claims (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_reference TEXT UNIQUE NOT NULL,
    -- CLM-20260125-XXXX
    client_id INTEGER NOT NULL,
    store_id INTEGER,
    order_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    dispute_type TEXT NOT NULL,
    -- late_delivery, lost, damaged, invalid_pod
    amount_requested REAL NOT NULL,
    currency TEXT DEFAULT 'EUR',
    status TEXT DEFAULT 'pending',
    -- pending, submitted, under_review, accepted, rejected, paid
    submitted_at TIMESTAMP,
    response_deadline DATE,
    response_received_at TIMESTAMP,
    accepted_amount REAL,
    rejection_reason TEXT,
    payment_status TEXT DEFAULT 'unpaid',
    -- unpaid, processing, paid
    payment_date TIMESTAMP,
    success_probability REAL,
    -- Score de 0 à 1 au moment du dépôt
    predicted_days_to_recovery INTEGER,
    -- Metadata
    order_date DATE,
    tracking_number TEXT,
    customer_name TEXT,
    delivery_address TEXT,
    -- Automation
    skill_used TEXT,
    -- chronopost_claim, colissimo_claim, etc.
    automation_status TEXT,
    -- manual, automated, failed
    automation_error TEXT,
    -- Photos/Evidence
    evidence_uploaded BOOLEAN DEFAULT 0,
    evidence_count INTEGER DEFAULT 0,
    -- Follow-up & Escalation
    follow_up_level INTEGER DEFAULT 0,
    -- 0: none, 1: status_request, 2: warning, 3: formal_notice
    last_follow_up_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE
    SET NULL
);
CREATE INDEX IF NOT EXISTS idx_claims_reference ON claims(claim_reference);
CREATE INDEX IF NOT EXISTS idx_claims_client ON claims(client_id);
CREATE INDEX IF NOT EXISTS idx_claims_status ON claims(status);
CREATE INDEX IF NOT EXISTS idx_claims_payment ON claims(payment_status);
CREATE INDEX IF NOT EXISTS idx_claims_submitted ON claims(submitted_at);
-- Table: Disputes (Détections de litiges)
CREATE TABLE IF NOT EXISTS disputes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    store_id INTEGER,
    order_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    dispute_type TEXT NOT NULL,
    amount_recoverable REAL NOT NULL,
    currency TEXT DEFAULT 'EUR',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    claim_id INTEGER,
    -- NULL si pas encore réclamé
    is_claimed BOOLEAN DEFAULT 0,
    success_probability REAL,
    -- Score de 0 à 1 (AI Predictor)
    predicted_days_to_recovery INTEGER,
    -- Délai estimé via IA
    -- Order details
    order_date DATE,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    tracking_number TEXT,
    customer_name TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (store_id) REFERENCES stores(id) ON DELETE
    SET NULL,
        FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE
    SET NULL
);
CREATE INDEX IF NOT EXISTS idx_disputes_client ON disputes(client_id);
CREATE INDEX IF NOT EXISTS idx_disputes_claimed ON disputes(is_claimed);
CREATE INDEX IF NOT EXISTS idx_disputes_detected ON disputes(detected_at);
-- Table: Payments (Historique paiements)
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    claim_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    client_share REAL NOT NULL,
    -- 80%
    platform_fee REAL NOT NULL,
    -- 20%
    commission_amount REAL,
    -- Montant exact prélevé (peut varier si promo/frais)
    currency TEXT DEFAULT 'EUR',
    payment_method TEXT,
    -- stripe_connect, manual_transfer
    payment_status TEXT DEFAULT 'pending',
    -- pending, processing, completed, failed
    transaction_reference TEXT,
    stripe_transfer_id TEXT,
    paid_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_payments_claim ON payments(claim_id);
CREATE INDEX IF NOT EXISTS idx_payments_client ON payments(client_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(payment_status);
-- Table: Notifications (Emails envoyés)
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,
    -- welcome, claim_submitted, claim_accepted, disputes_detected
    subject TEXT NOT NULL,
    sent_to TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'sent',
    -- sent, failed, bounced
    error_message TEXT,
    related_claim_id INTEGER,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (related_claim_id) REFERENCES claims(id) ON DELETE
    SET NULL
);
CREATE INDEX IF NOT EXISTS idx_notifications_client ON notifications(client_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_sent ON notifications(sent_at);
-- Table: Activity Logs (Pour audit et RGPD)
CREATE TABLE IF NOT EXISTS activity_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER,
    action TEXT NOT NULL,
    -- login, claim_submitted, data_exported, etc.
    resource_type TEXT,
    -- claim, payment, store
    resource_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    -- JSON
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE
    SET NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_client ON activity_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON activity_logs(timestamp);
-- Table: System Alerts (Anti-Bypass & Issues)
CREATE TABLE IF NOT EXISTS system_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    -- bypass_detected, api_error, payment_issue
    severity TEXT DEFAULT 'medium',
    -- low, medium, high, critical
    message TEXT NOT NULL,
    related_resource_type TEXT,
    related_resource_id INTEGER,
    is_resolved BOOLEAN DEFAULT 0,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON system_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON system_alerts(alert_type);
-- Table: Global Fraud Registry (Shared Reputation)
CREATE TABLE IF NOT EXISTS global_fraud_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    -- email, phone, address, ip
    entity_value TEXT NOT NULL,
    risk_level TEXT DEFAULT 'medium',
    -- low, medium, high, critical
    reason TEXT,
    reported_by_client_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_value)
);
CREATE INDEX IF NOT EXISTS idx_fraud_entity ON global_fraud_registry(entity_value);
-- Table: System Settings
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Valeurs par défaut
INSERT
    OR IGNORE INTO system_settings (key, value, description)
VALUES (
        'platform_commission_rate',
        '0.20',
        'Taux de commission plateforme (20%)'
    ),
    (
        'email_digest_enabled',
        '1',
        'Activer emails digest quotidiens'
    ),
    (
        'auto_submit_claims',
        '0',
        'Soumission automatique des réclamations'
    ),
    (
        'stripe_mode',
        'test',
        'Mode Stripe (test ou live)'
    );
-- Vue: Statistiques clients
CREATE VIEW IF NOT EXISTS client_statistics AS
SELECT c.id as client_id,
    c.email,
    COUNT(DISTINCT cl.id) as total_claims,
    SUM(
        CASE
            WHEN cl.status = 'accepted' THEN 1
            ELSE 0
        END
    ) as accepted_claims,
    SUM(
        CASE
            WHEN cl.status = 'rejected' THEN 1
            ELSE 0
        END
    ) as rejected_claims,
    SUM(
        CASE
            WHEN cl.status = 'pending' THEN 1
            ELSE 0
        END
    ) as pending_claims,
    SUM(cl.amount_requested) as total_requested,
    SUM(
        CASE
            WHEN cl.status = 'accepted' THEN cl.accepted_amount
            ELSE 0
        END
    ) as total_recovered,
    SUM(
        CASE
            WHEN p.payment_status = 'completed' THEN p.client_share
            ELSE 0
        END
    ) as total_paid_to_client,
    COUNT(DISTINCT d.id) as total_disputes_detected
FROM clients c
    LEFT JOIN claims cl ON c.id = cl.client_id
    LEFT JOIN payments p ON c.id = p.client_id
    LEFT JOIN disputes d ON c.id = d.client_id
GROUP BY c.id,
    c.email;