-- Add Strategy Tool Credits
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS strategy_closer_credits INTEGER DEFAULT 0;

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS strategy_followup_credits INTEGER DEFAULT 0;

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS strategy_plan_credits INTEGER DEFAULT 0;

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS strategy_inquisitor_credits INTEGER DEFAULT 0;

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS credits_linkedin INTEGER DEFAULT 0;

-- Verify
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users';
