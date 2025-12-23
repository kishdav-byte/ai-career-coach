DROP VIEW IF EXISTS user_recent_activity;

CREATE VIEW user_recent_activity AS
SELECT 
    user_id,
    'Resume Analysis' as project_name,
    'resume' as type,
    overall_score as score,
    created_at,
    'Completed' as status
FROM resumes
UNION ALL
SELECT 
    user_id,
    'Mock Interview' as project_name,
    'interview' as type,
    overall_score as score,
    created_at,
    'Completed' as status
FROM interviews
UNION ALL
SELECT 
    u.id as user_id, 
    'LinkedIn Optimization' as project_name,
    'linkedin' as type,
    NULL as score,
    a.created_at,
    COALESCE(a.metadata->>'status', 'Completed') as status
FROM activity_logs a
JOIN users u ON a.user_email = u.email
WHERE a.feature = 'linkedin_optimize';
