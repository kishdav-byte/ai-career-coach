-- 1. Enable RLS on the table (Safe to run even if already enabled)
ALTER TABLE user_jobs ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing policies to ensure a clean slate (Prevents conflicts)
DROP POLICY IF EXISTS "Users can view their own jobs" ON user_jobs;
DROP POLICY IF EXISTS "Users can insert their own jobs" ON user_jobs;
DROP POLICY IF EXISTS "Users can update their own jobs" ON user_jobs;
DROP POLICY IF EXISTS "Users can delete their own jobs" ON user_jobs;

-- 3. Create comprehensive policies

-- SELECT: Allow users to view ONLY their own rows
CREATE POLICY "Users can view their own jobs"
ON user_jobs
FOR SELECT
TO authenticated
USING (auth.uid() = user_id);

-- INSERT: Allow users to insert rows ONLY if they own them
-- Note: The backend must send the correct 'user_id' which matches the auth token
CREATE POLICY "Users can insert their own jobs"
ON user_jobs
FOR INSERT
TO authenticated
WITH CHECK (auth.uid() = user_id);

-- UPDATE: Allow users to update ONLY their own rows
CREATE POLICY "Users can update their own jobs"
ON user_jobs
FOR UPDATE
TO authenticated
USING (auth.uid() = user_id)
WITH CHECK (auth.uid() = user_id);

-- DELETE: Allow users to delete ONLY their own rows
CREATE POLICY "Users can delete their own jobs"
ON user_jobs
FOR DELETE
TO authenticated
USING (auth.uid() = user_id);

-- Optional: Ensure user_id defaults to the current auth user if not provided
-- ALTER TABLE user_jobs ALTER COLUMN user_id SET DEFAULT auth.uid();
