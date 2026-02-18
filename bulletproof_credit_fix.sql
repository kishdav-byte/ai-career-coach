-- 🚀 ACE INTERVIEW: UNIVERSAL CREDIT RECOVERY SCRIPT (v3.0)
-- This script is "bulletproof". It checks for every legacy column individually.
-- Run this in the Supabase SQL Editor.

BEGIN;

-- 1. Create standardized columns if they don't exist
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_interview INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_resume INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_cover INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_linkedin INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_followup INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_negotiation INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_inquisitor INTEGER DEFAULT 0;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS credits_30_60_90 INTEGER DEFAULT 0;

-- 2. SAFE MIGRATION
DO $$
BEGIN
    -- Move Interview Credits
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='interview_credits') THEN
        UPDATE public.users SET credits_interview = credits_interview + COALESCE(interview_credits, 0), interview_credits = 0;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='credits_interview_sim') THEN
        UPDATE public.users SET credits_interview = credits_interview + COALESCE(credits_interview_sim, 0), credits_interview_sim = 0;
    END IF;

    -- Move Resume/Rewrite
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='rewrite_credits') THEN
        UPDATE public.users SET credits_resume = credits_resume + COALESCE(rewrite_credits, 0), rewrite_credits = 0;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='resume_credits') THEN
        UPDATE public.users SET credits_resume = credits_resume + COALESCE(resume_credits, 0), resume_credits = 0;
    END IF;

    -- Move Cover Letter
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='credits_cover_letter') THEN
        UPDATE public.users SET credits_cover = credits_cover + COALESCE(credits_cover_letter, 0), credits_cover_letter = 0;
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='strategy_cover_credits') THEN
        UPDATE public.users SET credits_cover = credits_cover + COALESCE(strategy_cover_credits, 0), strategy_cover_credits = 0;
    END IF;

    -- Move Follow-Up
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='strategy_followup_credits') THEN
        UPDATE public.users SET credits_followup = credits_followup + COALESCE(strategy_followup_credits, 0), strategy_followup_credits = 0;
    END IF;

    -- Move Closer
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='credits_closer') THEN
        UPDATE public.users SET credits_negotiation = credits_negotiation + COALESCE(credits_closer, 0), credits_closer = 0;
    END IF;

END $$;

COMMIT;

-- ✅ SUCCESS: Check your balance:
-- SELECT email, credits_interview, credits_resume, credits_cover FROM users;
