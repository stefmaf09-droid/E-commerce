-- ================================================
-- Schéma PostgreSQL - Recours E-commerce (Neon)
-- Converti depuis schema.sql (SQLite)
-- ================================================
-- Table: Clients
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    company_name TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    stripe_account_id TEXT UNIQUE,
    stripe_onboarding_completed BOOLEAN DEFAULT FALSE,
    stripe_connect_id TEXT UNIQUE,
    stripe_onboarding_status TEXT DEFAULT 'pending',
    subscription_tier TEXT DEFAULT 'standard',
    commission_rate REAL DEFAULT 20.0,
    notification_preferences TEXT
);
CREATE INDEX IF NOT EXISTS idx_clients_email ON clients(email);
CREATE INDEX IF NOT EXISTS idx_clients_stripe ON clients(stripe_account_id);
-- Table: Stores
CREATE TABLE IF NOT EXISTS stores (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    platform TEXT NOT NULL,
    store_name TEXT NOT NULL,
    store_url TEXT,
    country TEXT DEFAULT 'FR',
    currency TEXT DEFAULT 'EUR',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_stores_client ON stores(client_id);
-- Table: Claims
CREATE TABLE IF NOT EXISTS claims (
    id SERIAL PRIMARY KEY,
    claim_reference TEXT UNIQUE NOT NULL,
    client_id INTEGER NOT NULL,
    store_id INTEGER,
    order_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    dispute_type TEXT NOT NULL,
    amount_requested REAL NOT NULL,
    currency TEXT DEFAULT 'EUR',
    status TEXT DEFAULT 'pending',
    submitted_at TIMESTAMP,
    response_deadline DATE,
    response_received_at TIMESTAMP,
    accepted_amount REAL,
    rejection_reason TEXT,
    payment_status TEXT DEFAULT 'unpaid',
    payment_date TIMESTAMP,
    success_probability REAL,
    predicted_days_to_recovery INTEGER,
    order_date DATE,
    tracking_number TEXT,
    customer_name TEXT,
    delivery_address TEXT,
    skill_used TEXT,
    automation_status TEXT,
    automation_error TEXT,
    evidence_uploaded BOOLEAN DEFAULT FALSE,
    evidence_count INTEGER DEFAULT 0,
    follow_up_level INTEGER DEFAULT 0,
    last_follow_up_at TIMESTAMP,
    pod_fetch_status TEXT,
    pod_url TEXT,
    pod_fetched_at TIMESTAMP,
    pod_delivery_person TEXT,
    pod_fetch_error TEXT,
    ai_reason_key TEXT,
    ai_advice TEXT,
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
-- Table: Disputes
CREATE TABLE IF NOT EXISTS disputes (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    store_id INTEGER,
    order_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    dispute_type TEXT NOT NULL,
    amount_recoverable REAL NOT NULL,
    currency TEXT DEFAULT 'EUR',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    claim_id INTEGER,
    is_claimed BOOLEAN DEFAULT FALSE,
    success_probability REAL,
    predicted_days_to_recovery INTEGER,
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
-- Table: Payments
CREATE TABLE IF NOT EXISTS payments (
    id SERIAL PRIMARY KEY,
    claim_id INTEGER NOT NULL,
    client_id INTEGER NOT NULL,
    total_amount REAL NOT NULL,
    client_share REAL NOT NULL,
    platform_fee REAL NOT NULL,
    commission_amount REAL,
    currency TEXT DEFAULT 'EUR',
    payment_method TEXT,
    payment_status TEXT DEFAULT 'pending',
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
-- Table: Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL,
    notification_type TEXT NOT NULL,
    subject TEXT NOT NULL,
    sent_to TEXT NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'sent',
    error_message TEXT,
    related_claim_id INTEGER,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE CASCADE,
    FOREIGN KEY (related_claim_id) REFERENCES claims(id) ON DELETE
    SET NULL
);
CREATE INDEX IF NOT EXISTS idx_notifications_client ON notifications(client_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_sent ON notifications(sent_at);
-- Table: Activity Logs
CREATE TABLE IF NOT EXISTS activity_logs (
    id SERIAL PRIMARY KEY,
    client_id INTEGER,
    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(id) ON DELETE
    SET NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_client ON activity_logs(client_id);
CREATE INDEX IF NOT EXISTS idx_logs_action ON activity_logs(action);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON activity_logs(timestamp);
-- Table: System Alerts
CREATE TABLE IF NOT EXISTS system_alerts (
    id SERIAL PRIMARY KEY,
    alert_type TEXT NOT NULL,
    severity TEXT DEFAULT 'medium',
    message TEXT NOT NULL,
    related_resource_type TEXT,
    related_resource_id INTEGER,
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alerts_unresolved ON system_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_alerts_type ON system_alerts(alert_type);
-- Table: Global Fraud Registry
CREATE TABLE IF NOT EXISTS global_fraud_registry (
    id SERIAL PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_value TEXT NOT NULL,
    risk_level TEXT DEFAULT 'medium',
    reason TEXT,
    reported_by_client_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(entity_type, entity_value)
);
CREATE INDEX IF NOT EXISTS idx_fraud_entity ON global_fraud_registry(entity_value);
-- Table: Webhook Events
CREATE TABLE IF NOT EXISTS webhook_events (
    id SERIAL PRIMARY KEY,
    tracking_number TEXT NOT NULL,
    event_tag TEXT NOT NULL,
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload_json TEXT,
    UNIQUE(tracking_number, event_tag)
);
CREATE INDEX IF NOT EXISTS idx_webhook_tracking ON webhook_events(tracking_number);
-- Table: System Settings
CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO system_settings (key, value, description)
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
    ) ON CONFLICT (key) DO NOTHING;
-- Vue: Statistiques clients
CREATE OR REPLACE VIEW client_statistics AS
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