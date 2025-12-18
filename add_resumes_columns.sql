-- Add missing columns to 'resumes' table to support full analysis saving
ALTER TABLE public.resumes 
ADD COLUMN IF NOT EXISTS job_title TEXT,
ADD COLUMN IF NOT EXISTS content JSONB,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Verify existence of other columns just in case
-- (e.g. overall_score, user_id should already exist based on screenshot)
