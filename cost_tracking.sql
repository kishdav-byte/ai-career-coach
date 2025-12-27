-- TASK 1: Cost Tracking Columns
ALTER TABLE public.system_logs ADD COLUMN IF NOT EXISTS tokens_used INT DEFAULT 0;
ALTER TABLE public.system_logs ADD COLUMN IF NOT EXISTS estimated_cost NUMERIC(10, 6) DEFAULT 0.000000;

-- Optional: Create an index for faster cost aggregation
-- CREATE INDEX idx_sys_logs_created_at ON public.system_logs(created_at);
