-- Add stripe_customer_id column to users table
-- This stores the Stripe Customer ID for each user, enabling:
-- 1. Faster checkout (no need to create customer each time)
-- 2. Subscription management
-- 3. Customer history and analytics
-- 4. Saved payment methods

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer_id 
ON users(stripe_customer_id);

-- Add comment for documentation
COMMENT ON COLUMN users.stripe_customer_id IS 'Stripe Customer ID (cus_xxx) for payment processing and subscription management';
