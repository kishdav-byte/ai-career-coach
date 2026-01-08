-- Fix Column Name Mismatch for Value Follow-Up
-- Code expects 'credits_followup'
-- DB might have 'strategy_followup_credits'

DO $$
BEGIN
  IF EXISTS(SELECT * FROM information_schema.columns WHERE table_name='users' AND column_name='strategy_followup_credits') THEN
      ALTER TABLE public.users RENAME COLUMN strategy_followup_credits TO credits_followup;
  ELSIF NOT EXISTS(SELECT * FROM information_schema.columns WHERE table_name='users' AND column_name='credits_followup') THEN
      ALTER TABLE public.users ADD COLUMN credits_followup INTEGER DEFAULT 0;
  END IF;
END $$;
