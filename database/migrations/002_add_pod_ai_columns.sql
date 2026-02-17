-- Migration: Add POD and AI Analysis columns to claims table
-- Date: 2026-02-14
-- Description: Adds columns for POD (Proof of Delivery) tracking and AI analysis
-- For PostgreSQL
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_fetch_status TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_url TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_fetched_at TIMESTAMP;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_delivery_person TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_fetch_error TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS ai_reason_key TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS ai_advice TEXT;
-- Add comments for documentation
COMMENT ON COLUMN claims.pod_fetch_status IS 'Status of POD fetch: null (not requested), pending, success, failed';
COMMENT ON COLUMN claims.pod_url IS 'URL to download the proof of delivery document';
COMMENT ON COLUMN claims.pod_fetched_at IS 'Timestamp when POD was successfully fetched';
COMMENT ON COLUMN claims.pod_delivery_person IS 'Name of person who received the package (from POD)';
COMMENT ON COLUMN claims.pod_fetch_error IS 'Error message if POD fetch failed';
COMMENT ON COLUMN claims.ai_reason_key IS 'AI-detected refusal reason key (bad_signature, weight_match, etc.)';
COMMENT ON COLUMN claims.ai_advice IS 'AI-generated advice for handling this claim';