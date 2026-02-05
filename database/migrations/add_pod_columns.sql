-- Add POD auto-fetch columns to claims table
-- Run this migration to enable automatic POD retrieval
-- Add POD-related columns
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_url TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_fetch_status TEXT DEFAULT 'pending';
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_fetch_error TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_fetched_at TIMESTAMP;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_signature_url TEXT;
ALTER TABLE claims
ADD COLUMN IF NOT EXISTS pod_delivery_person TEXT;
-- pod_fetch_status values:
-- 'pending': Not yet attempted
-- 'fetching': API call in progress
-- 'success': POD retrieved successfully
-- 'failed': API error (need manual upload)
-- 'not_available': Carrier doesn't provide PODs
-- 'manual': User uploaded manually (skip auto-fetch)
-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_claims_pod_status ON claims(pod_fetch_status);
-- Migration complete