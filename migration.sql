-- Migration: Add Role Column for Admin Access
-- Run this in your Supabase SQL Editor

-- 1. Add 'role' column to users table if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';

-- 2. (Optional) Set your specific email as admin immediately
-- Replace 'your_email@example.com' with your actual login email
UPDATE users 
SET role = 'admin' 
WHERE email = 'your_email@example.com';

-- 3. Verify the change
SELECT * FROM users WHERE role = 'admin';

-- ==========================================
-- NEW: Chat Logs for Transcript Viewer
-- ==========================================

CREATE TABLE IF NOT EXISTS chat_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email TEXT NOT NULL,
    message TEXT,
    response TEXT,
    feature TEXT DEFAULT 'interview',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for faster lookups by user
CREATE INDEX IF NOT EXISTS idx_chat_logs_email ON chat_logs(user_email);
