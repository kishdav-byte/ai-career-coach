-- Create a TEMPORARY view for testing (or just a new view name to avoid conflicts)
-- We will call it 'test_user_recent_activity' matching the structure of the dashboard query

CREATE OR REPLACE VIEW test_user_recent_activity AS

-- 1. Resumes
SELECT 
    user_id,
    'Resume Analysis' as project_name,
    'resume' as type,
    overall_score as score,
    created_at,
    'Completed' as status
FROM resumes

UNION ALL

-- 2. Interviews
SELECT 
    user_id,
    'Mock Interview' as project_name,
    'interview' as type,
    overall_score as score,
    created_at,
    'Completed' as status
FROM interviews

UNION ALL

-- 3. LinkedIn Optimization (From Activity Logs)
-- We map 'success' to a generic score of 100 or NULL, and feature to project_name
SELECT 
    (SELECT id FROM users WHERE email = user_email LIMIT 1) as user_id, 
    'LinkedIn Optimization' as project_name,
    'linkedin' as type,
    NULL as score, -- No numeric score for text rewrite
    created_at,
    (metadata->>'status') as status
FROM activity_logs
WHERE feature = 'linkedin_optimize';
