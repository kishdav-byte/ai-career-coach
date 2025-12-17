-- Add Universal 'credits' column
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS credits INTEGER DEFAULT 0;

-- Ensure role_reversal_count exists (for 3-Tier logic)
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS role_reversal_count INTEGER DEFAULT 0;

-- OPTIONAL: Data Migration (Consolidate Legacy Credits)
-- Run this if you want to convert existing specific credits to Universal Credits.
-- Uncomment to execute:
/*
UPDATE public.users
SET credits = credits + 
              COALESCE(resume_credits, 0) + 
              COALESCE(interview_credits, 0) + 
              COALESCE(rewrite_credits, 0) + 
              COALESCE(credits_cover_letter, 0) + 
              COALESCE(credits_linkedin, 0) + 
              COALESCE(credits_negotiation, 0) + 
              COALESCE(credits_inquisitor, 0) + 
              COALESCE(credits_followup, 0) + 
              COALESCE(credits_30_60_90, 0) + 
              COALESCE(credits_interview_sim, 0);

-- Zero out legacy columns after migration?
-- UPDATE public.users SET resume_credits = 0, interview_credits = 0, ...;
*/

-- Verify
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users';
