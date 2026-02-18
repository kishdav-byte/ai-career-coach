-- 🚀 ACE INTERVIEW: TOTAL CREDIT RECONCILIATION SCRIPT (v2.0)
-- This script safely migrates all legacy credits to the new standardized schema.
-- Run this in the Supabase SQL Editor.

BEGIN;

-- 1. Ensure all NEW standardized columns exist
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_interview INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_resume INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_cover INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_linkedin INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_followup INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_negotiation INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_inquisitor INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_30_60_90 INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_unlimited BOOLEAN DEFAULT FALSE;

-- 2. SMART CONSOLIDATION (Safe check for legacy columns)
DO $$
BEGIN
    -- INTERVIEW CREDITS
    UPDATE public.users SET credits_interview = credits_interview + COALESCE(interview_credits, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='interview_credits');

    UPDATE public.users SET credits_interview = credits_interview + COALESCE(credits_interview_sim, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='credits_interview_sim');

    -- RESUME / REWRITE CREDITS
    UPDATE public.users SET credits_resume = credits_resume + COALESCE(rewrite_credits, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='rewrite_credits');

    UPDATE public.users SET credits_resume = credits_resume + COALESCE(resume_credits, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='resume_credits');

    -- COVER LETTER CREDITS
    UPDATE public.users SET credits_cover = credits_cover + COALESCE(credits_cover_letter, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='credits_cover_letter');

    UPDATE public.users SET credits_cover = credits_cover + COALESCE(strategy_cover_credits, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='strategy_cover_credits');

    -- FOLLOW-UP CREDITS
    UPDATE public.users SET credits_followup = credits_followup + COALESCE(strategy_followup_credits, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='strategy_followup_credits');

    -- NEGOTIATION / CLOSER CREDITS
    UPDATE public.users SET credits_negotiation = credits_negotiation + COALESCE(credits_closer, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='credits_closer');

    -- LINKEDIN CREDITS
    UPDATE public.users SET credits_linkedin = credits_linkedin + COALESCE(linkedin_credits, 0)
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='linkedin_credits');

END $$;

-- 3. RESET LEGACY COLUMNS (Optional: set to 0 to prevent double migration)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='interview_credits') THEN
        UPDATE public.users SET interview_credits = 0;
    END IF;
    -- Add more resets here if you want to be clean.
END $$;

COMMIT;

-- ✅ SUCCESS: Check your balance now with: 
-- SELECT email, credits_interview, credits_resume, credits_cover FROM users;
