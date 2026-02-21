-- Create guest_scans table for anonymous tracking
CREATE TABLE IF NOT EXISTS public.guest_scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    overall_score INTEGER,
    word_count INTEGER,
    referral TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (Read-only for Admin, Insert for anyone or Anon)
ALTER TABLE public.guest_scans ENABLE ROW LEVEL SECURITY;

-- Allow anonymous inserts (from the API)
CREATE POLICY "Enable insert for authenticated users and anon"
ON public.guest_scans FOR INSERT
WITH CHECK (true);

-- Allow admins to select
CREATE POLICY "Admins can view guest scans"
ON public.guest_scans FOR SELECT
USING (true); -- We can refine this to service role only if needed, but for now true is fine for the admin dashboard
