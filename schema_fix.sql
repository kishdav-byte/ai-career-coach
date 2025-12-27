-- TASK 2: Add Missing Columns to Existing Tables

-- 1. Add focus_areas to user_jobs (for Mission Brief feature)
ALTER TABLE public.user_jobs 
ADD COLUMN IF NOT EXISTS focus_areas jsonb;

-- 2. Add cost tracking columns to error_logs (for OpenAI spend tracking)
ALTER TABLE public.error_logs 
ADD COLUMN IF NOT EXISTS tokens_used int DEFAULT 0;

ALTER TABLE public.error_logs 
ADD COLUMN IF NOT EXISTS estimated_cost numeric(10, 6) DEFAULT 0.000000;

-- Optional: Add index for faster cost queries
CREATE INDEX IF NOT EXISTS idx_error_logs_created_at ON public.error_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_error_logs_cost ON public.error_logs(estimated_cost) WHERE estimated_cost > 0;
