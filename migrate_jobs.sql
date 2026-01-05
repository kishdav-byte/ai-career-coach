-- 1. MIGRATE DATA (Copy from old table to new table)
-- We map 'job_title' -> 'role_title' and normalize statuses.

INSERT INTO job_tracker (user_id, role_title, company_name, status, job_description, notes, salary_target, created_at)
SELECT 
    user_id, 
    job_title, 
    company_name, 
    CASE 
        WHEN status = 'Identified' THEN 'Engage'
        WHEN status = 'Applied' THEN 'Engage' 
        WHEN status = 'Offer' THEN 'Post Interview'
        ELSE status 
    END, 
    job_description, 
    notes, 
    salary_target,
    created_at
FROM user_jobs;

-- 2. ENABLE ROW LEVEL SECURITY (RLS)
ALTER TABLE job_tracker ENABLE ROW LEVEL SECURITY;

-- 3. CREATE POLICIES (Secure the table)

-- Policy: Users can see only their own jobs
CREATE POLICY "Users can view their own tracked jobs"
ON job_tracker FOR SELECT
USING (auth.uid() = user_id);

-- Policy: Users can add their own jobs
CREATE POLICY "Users can insert their own tracked jobs"
ON job_tracker FOR INSERT
WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own jobs
CREATE POLICY "Users can update their own tracked jobs"
ON job_tracker FOR UPDATE
USING (auth.uid() = user_id);

-- Policy: Users can delete their own jobs
CREATE POLICY "Users can delete their own tracked jobs"
ON job_tracker FOR DELETE
USING (auth.uid() = user_id);
