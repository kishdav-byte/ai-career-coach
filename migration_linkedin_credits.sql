-- Add credits_linkedin column to users table if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS credits_linkedin INTEGER DEFAULT 0;

-- Comment on column
COMMENT ON COLUMN users.credits_linkedin IS 'Specific credits for LinkedIn Profile Optimization tool';
