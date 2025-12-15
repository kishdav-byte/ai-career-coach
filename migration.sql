-- Add Credit Columns for Strategy Lab Tools (Phase 2)
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_inquisitor INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_followup INTEGER DEFAULT 0;

-- Ensure credits_negotiation exists (Phase 1)
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_negotiation INTEGER DEFAULT 0;
