-- Migration: Admin Console Support (Role, Chat Logs, Error Logs, Activity Logs)
-- Run this in your Supabase SQL Editor

-- 1. Add 'role' column to users table if it doesn't exist
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'user';

-- 2. (Optional) Set your specific email as admin immediately
-- Replace 'your_email@example.com' with your actual login email
UPDATE users 
SET role = 'admin' 
WHERE email = 'your_email@example.com';

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

CREATE INDEX IF NOT EXISTS idx_chat_logs_email ON chat_logs(user_email);

-- ==========================================
-- NEW: Error Logs for Recent Errors Widget
-- ==========================================

CREATE TABLE IF NOT EXISTS error_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email TEXT, -- Can be null for system errors
    error_type TEXT NOT NULL,
    details TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- NEW: Activity Logs for Activity Chart
-- ==========================================

CREATE TABLE IF NOT EXISTS activity_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_email TEXT NOT NULL,
    feature TEXT NOT NULL, -- 'resume_analysis', 'interview_coach', 'chat_bot'
    metadata JSONB, -- Optional extra data
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_logs(created_at);

-- ==========================================
-- NEW: Sync Auth Users to Public Users
-- (Fixes "Total Users" not updating)
-- ==========================================

-- Function to handle new user signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, name, created_at)
  values (new.id, new.email, new.raw_user_meta_data->>'full_name', new.created_at);
  return new;
end;
$$ language plpgsql security definer;

-- Trigger to call the function on insert
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- ==========================================
-- NEW: Row Level Security (RLS) for Admins
-- (Fixes "Console Empty" issue & Recursion Error)
-- ==========================================

-- Enable RLS on users table
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Allow users to see their own data
DROP POLICY IF EXISTS "Users can see own data" ON users;
CREATE POLICY "Users can see own data" ON users FOR SELECT USING (auth.uid() = id);

-- HELPER: Check Admin status safely (Bypasses RLS to avoid recursion)
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM public.users
    WHERE email = auth.jwt()->>'email'
    AND role = 'admin'
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Allow Admins to see ALL data (Existing policy might need to be dropped first)
DROP POLICY IF EXISTS "Admins can see all data" ON users;
CREATE POLICY "Admins can see all data" ON users FOR SELECT USING (
  public.is_admin()
);
