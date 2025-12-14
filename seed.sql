-- Seed Data for Admin Dashboard
-- Run this in Supabase if you want to see the charts populated immediately with sample data.

-- 1. Activity Logs (Populates the Bar Graph)
INSERT INTO activity_logs (user_email, feature, created_at) VALUES 
('demo_user@example.com', 'resume_analysis', NOW()),
('demo_user@example.com', 'interview_coach', NOW()),
('demo_user@example.com', 'resume_analysis', NOW() - INTERVAL '1 day'),
('new_user@example.com', 'interview_coach', NOW() - INTERVAL '1 day'),
('new_user@example.com', 'interview_coach', NOW() - INTERVAL '1 day'),
('demo_user@example.com', 'chat_bot', NOW() - INTERVAL '2 days'),
('demo_user@example.com', 'resume_analysis', NOW() - INTERVAL '2 days'),
('vip_user@example.com', 'interview_coach', NOW() - INTERVAL '3 days'),
('vip_user@example.com', 'interview_coach', NOW() - INTERVAL '3 days'),
('demo_user@example.com', 'interview_coach', NOW() - INTERVAL '4 days'),
('new_user@example.com', 'resume_analysis', NOW() - INTERVAL '5 days'),
('demo_user@example.com', 'interview_coach', NOW() - INTERVAL '6 days');

-- 2. Error Logs (Populates the Recent Errors Widget)
INSERT INTO error_logs (user_email, error_type, details, created_at) VALUES
('test@example.com', 'Stripe_Declined', 'Card was declined by bank.', NOW() - INTERVAL '3 hours'),
('system_monitor', '500_Server_Error', 'Connection timeout to OpenAI API.', NOW() - INTERVAL '1 day'),
('upload_bot', 'Upload_Failed', 'File size exceeds limit (10MB).', NOW() - INTERVAL '2 days');

-- 3. Chat Logs (Populates the Transcript Viewer)
INSERT INTO chat_logs (user_email, message, response, feature, created_at) VALUES
('demo_user@example.com', 'Tell me about yourself', 'I have 5 years of experience in product management, leading cross-functional teams...', 'interview', NOW() - INTERVAL '10 minutes'),
('demo_user@example.com', 'What is your greatest weakness?', 'I sometimes focus too much on details, but I am learning to delegate...', 'interview', NOW() - INTERVAL '8 minutes');
