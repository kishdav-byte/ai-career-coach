-- Add monthly_voice_usage for Fair Use tracking
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS monthly_voice_usage INTEGER DEFAULT 0;

-- Ensure stripe_customer_id exists (for Webhook lookup)
ALTER TABLE public.users
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;

-- Add Missing Credit Columns (if they don't exist) to fix 500 Error
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS resume_credits INTEGER DEFAULT 0;

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS interview_credits INTEGER DEFAULT 0;

ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS rewrite_credits INTEGER DEFAULT 0;

-- Verify columns
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'users';
