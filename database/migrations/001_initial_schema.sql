-- Agent IA Recouvrement - Initial Schema
-- PostgreSQL Migration v1.0
-- Created: 2026-01-21

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- Clients Table
-- ===========================================
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    company_name VARCHAR(255),
    platform VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT clients_email_check CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$')
);

CREATE INDEX idx_clients_email ON clients(email);
CREATE INDEX idx_clients_status ON clients(status);

-- ===========================================
-- Credentials Table (Encrypted)
-- ===========================================
CREATE TABLE credentials (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,
    encrypted_data TEXT NOT NULL,
    encryption_version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE INDEX idx_credentials_client ON credentials(client_id);
CREATE UNIQUE INDEX idx_credentials_client_platform ON credentials(client_id, platform);

-- ===========================================
-- Orders Table
-- ===========================================
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    order_id VARCHAR(100) NOT NULL,
    platform_order_id VARCHAR(255),
    tracking_number VARCHAR(100),
    carrier VARCHAR(50),
    status VARCHAR(50),
    order_date TIMESTAMP,
    delivery_date TIMESTAMP,
    expected_delivery_date TIMESTAMP,
    total_amount DECIMAL(10, 2),
    shipping_cost DECIMAL(10, 2),
    customer_email VARCHAR(255),
    shipping_address JSONB,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT orders_client_order_unique UNIQUE(client_id, order_id)
);

CREATE INDEX idx_orders_client ON orders(client_id);
CREATE INDEX idx_orders_tracking ON orders(tracking_number);
CREATE INDEX idx_orders_carrier ON orders(carrier);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_date ON orders(order_date);

-- ===========================================
-- Disputes Table
-- ===========================================
CREATE TABLE disputes (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    dispute_type VARCHAR(50) NOT NULL,
    severity_score DECIMAL(3, 2) CHECK (severity_score >= 0 AND severity_score <= 1),
    reason TEXT,
    recoverable_amount DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'detected',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolution_type VARCHAR(50),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_disputes_client ON disputes(client_id);
CREATE INDEX idx_disputes_order ON disputes(order_id);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_type ON disputes(dispute_type);
CREATE INDEX idx_disputes_detected_at ON disputes(detected_at);

-- ===========================================
-- Claims Table
-- ===========================================
CREATE TABLE claims (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    dispute_id INTEGER REFERENCES disputes(id) ON DELETE CASCADE,
    claim_reference VARCHAR(100) UNIQUE,
    carrier VARCHAR(50) NOT NULL,
    tracking_number VARCHAR(100),
    claim_text TEXT,
    claim_value DECIMAL(10, 2),
    submission_method VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    amount_recovered DECIMAL(10, 2),
    client_share DECIMAL(10, 2),
    service_fee DECIMAL(10, 2),
    pod_analysis JSONB,
    confirmation_screenshot VARCHAR(500),
    confirmation_pdf VARCHAR(500),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_claims_dispute ON claims(dispute_id);
CREATE INDEX idx_claims_reference ON claims(claim_reference);
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_carrier ON claims(carrier);
CREATE INDEX idx_claims_submitted_at ON claims(submitted_at);

-- ===========================================
-- Notifications Table
-- ===========================================
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    uuid UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(255),
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}'::jsonb,
    read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX idx_notifications_client_unread ON notifications(client_id, read) WHERE read = FALSE;
CREATE INDEX idx_notifications_created_at ON notifications(created_at);

-- ===========================================
-- Analytics Cache Table
-- ===========================================
CREATE TABLE analytics_cache (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
    cache_key VARCHAR(100) NOT NULL,
    period VARCHAR(20),
    metrics JSONB NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    CONSTRAINT analytics_cache_client_key_unique UNIQUE(client_id, cache_key, period)
);

CREATE INDEX idx_analytics_client_period ON analytics_cache(client_id, period);

-- ===========================================
-- System Logs Table (for audit trail)
-- ===========================================
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id) ON DELETE SET NULL,
    level VARCHAR(20) NOT NULL,
    category VARCHAR(50),
    message TEXT,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_client ON system_logs(client_id);
CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_created_at ON system_logs(created_at);

-- ===========================================
-- Triggers for updated_at
-- ===========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_credentials_updated_at BEFORE UPDATE ON credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- Views for common queries
-- ===========================================

-- Active disputes with client info
CREATE VIEW active_disputes AS
SELECT 
    d.id,
    d.uuid,
    d.dispute_type,
    d.recoverable_amount,
    d.status,
    d.detected_at,
    c.email as client_email,
    c.name as client_name,
    o.tracking_number,
    o.carrier
FROM disputes d
JOIN clients c ON d.client_id = c.id
JOIN orders o ON d.order_id = o.id
WHERE d.status NOT IN ('resolved', 'cancelled', 'rejected');

-- Claims summary by client
CREATE VIEW client_claims_summary AS
SELECT 
    c.id as client_id,
    c.email,
    COUNT(cl.id) as total_claims,
    COUNT(CASE WHEN cl.status = 'accepted' THEN 1 END) as accepted_claims,
    SUM(cl.amount_recovered) as total_recovered,
    SUM(cl.client_share) as total_client_share,
    SUM(cl.service_fee) as total_fees
FROM clients c
LEFT JOIN disputes d ON c.id = d.client_id
LEFT JOIN claims cl ON d.id = cl.dispute_id
GROUP BY c.id, c.email;

-- ===========================================
-- Initial Data (Optional)
-- ===========================================

-- Example: Insert system status types
-- CREATE TABLE IF NOT EXISTS status_types (
--     status_code VARCHAR(50) PRIMARY KEY,
--     description TEXT
-- );

COMMENT ON TABLE clients IS 'E-commerce clients using the recovery service';
COMMENT ON TABLE credentials IS 'Encrypted API credentials for e-commerce platforms';
COMMENT ON TABLE orders IS 'Orders synchronized from client e-commerce platforms';
COMMENT ON TABLE disputes IS 'Detected delivery disputes requiring claims';
COMMENT ON TABLE claims IS 'Submitted claims to carriers for dispute resolution';
COMMENT ON TABLE notifications IS 'Real-time notifications for clients';
COMMENT ON TABLE analytics_cache IS 'Cached analytics metrics for performance';

-- Migration complete
SELECT 'Migration 001_initial_schema.sql completed successfully' AS status;
