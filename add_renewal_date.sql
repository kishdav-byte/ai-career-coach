-- Add subscription_period_end to track credit reset date
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS subscription_period_end TIMESTAMP WITH TIME ZONE;

-- Add comment for clarity
COMMENT ON COLUMN public.users.subscription_period_end IS 'The date when the current subscription period ends and credits reset.';
