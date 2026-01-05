-- 1. ADD COLUMN
ALTER TABLE user_jobs ADD COLUMN IF NOT EXISTS job_intel TEXT;

-- 2. MIGRATE EXISTING NOTES (One-time sync)
-- copying existing 'notes' to 'job_intel' so nothing is lost from previous entries
UPDATE user_jobs 
SET job_intel = notes 
WHERE job_intel IS NULL AND notes IS NOT NULL;

-- 3. VERIFY RLS (Just in case)
ALTER TABLE user_jobs ENABLE ROW LEVEL SECURITY;
