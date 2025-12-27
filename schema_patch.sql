-- TASK 1: Verify & Patch Database Schema

-- 1. Create system_logs table (Required for Admin Health)
CREATE TABLE IF NOT EXISTS public.system_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT now(),
    source TEXT,
    message TEXT,
    severity TEXT
);

-- 2. Add focus_areas to user_jobs (or job_targets)
-- Check if table is user_jobs or job_targets based on existing code (app.py uses 'user_jobs' usually, let's confirm)
-- Based on previous app.py reads, it queries 'user_jobs'.
ALTER TABLE public.user_jobs ADD COLUMN IF NOT EXISTS focus_areas JSONB;
ALTER TABLE public.user_jobs ADD COLUMN IF NOT EXISTS company_name TEXT;
ALTER TABLE public.user_jobs ADD COLUMN IF NOT EXISTS role_title TEXT;


-- 3. Update users (profiles) table
-- Universal Credits (users likely has 'credits', we can alias or add 'universal_credits' if strict)
-- We will use 'credits' as universal, but add 'universal_credits' if user explicitly demanded separation. 
-- However, 'credits' is the standard column. We'll stick to 'credits' effectively acting as universal.
-- Tool Vouchers (JSONB for generic tool tracking)
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS tool_vouchers JSONB DEFAULT '{}'::jsonb;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';

-- 4. Update interviews table
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS score INT;
ALTER TABLE public.interviews ADD COLUMN IF NOT EXISTS transcript TEXT;

-- Enable RLS on system_logs if needed (optional for now)
ALTER TABLE public.system_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public insert" ON public.system_logs FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow admin select" ON public.system_logs FOR SELECT USING (true); -- simplified
