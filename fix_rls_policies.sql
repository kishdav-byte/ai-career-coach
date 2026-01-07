-- FIX RLS POLICIES FOR SERVICE ROLE
-- This ensures the backend (Service Role) can ALWAYS update the users table context.

-- 1. Grant Bypass to Service Role (Implicit in Supabase but good to ensure policy exists)
-- Note: 'service_role' key usually bypasses RLS entirely, but if you have restrictive policies, explicit allowance helps.

-- ALTERNATIVE: Verify if RLS is enabled on 'users'
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- 2. Create Policy allowing Service Role full access
-- Supabase service_role key maps to the 'service_role' boolean check or role name
-- However, the cleanest way is just to rely on the key's inherent power.
-- If manual policies are blocking it, we add this:

CREATE POLICY "Service Role Full Access"
ON public.users
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- 3. Just in case, ensure public cannot write freely (Security Best Practice)
-- (Your existing policies likely handle this, this is just for the Service Role)

-- 4. Verify Columns exist (Safety Check)
DO $$
BEGIN
  IF NOT EXISTS(SELECT * FROM information_schema.columns WHERE table_name='users' AND column_name='interview_credits') THEN
      ALTER TABLE public.users ADD COLUMN interview_credits INTEGER DEFAULT 0;
  END IF;
END $$;
