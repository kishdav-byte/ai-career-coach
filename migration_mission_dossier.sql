-- Migration: Add Mission Dossier columns to user_jobs (or jobs) table

-- 1. Check if columns exist and add them if not
-- Note: Assuming table name is 'user_jobs' based on api/app.py, but user prompt said 'jobs'. 
-- The API uses 'user_jobs' in the code I viewed (line 2361), but let's check if 'jobs' is an alias or the actual name.
-- Previously in strategy-log.html it fetched from '/api/jobs'.
-- Based on api/app.py line 2361: supabase_admin.table('user_jobs').update(...)
-- So the table name is likely 'user_jobs'.

ALTER TABLE user_jobs 
ADD COLUMN IF NOT EXISTS job_description TEXT,
ADD COLUMN IF NOT EXISTS notes TEXT,
ADD COLUMN IF NOT EXISTS salary_target TEXT;

-- Verify
-- SELECT * FROM user_jobs LIMIT 1;
