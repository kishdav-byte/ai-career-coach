-- FIX: Create missing tables idempotently (handle existing policies/columns)

-- 1. Resume Scans Table
CREATE TABLE IF NOT EXISTS resume_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    score INT,
    resume_text TEXT,
    feedback JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure all columns exist (in case table was created partially)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='resume_scans' AND column_name='score') THEN
        ALTER TABLE resume_scans ADD COLUMN score INT;
    END IF;
END $$;

-- Policies: Drop first to avoid "already exists" error
DROP POLICY IF EXISTS "Users can insert their own scans" ON resume_scans;
DROP POLICY IF EXISTS "Users can view their own scans" ON resume_scans;

ALTER TABLE resume_scans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can insert their own scans" ON resume_scans FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view their own scans" ON resume_scans FOR SELECT USING (auth.uid() = user_id);


-- 2. Interviews Table
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    average_score INT,
    questions JSONB,
    transcript TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Ensure columns exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='interviews' AND column_name='average_score') THEN
        ALTER TABLE interviews ADD COLUMN average_score INT;
    END IF;
END $$;

-- Policies
DROP POLICY IF EXISTS "Users can insert their own interviews" ON interviews;
DROP POLICY IF EXISTS "Users can view their own interviews" ON interviews;

ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can insert their own interviews" ON interviews FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view their own interviews" ON interviews FOR SELECT USING (auth.uid() = user_id);
