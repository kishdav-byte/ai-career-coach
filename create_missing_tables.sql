-- Create missing 'resume_scans' table (used by Dashboard Resume Health)
CREATE TABLE IF NOT EXISTS resume_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    score INT,
    resume_text TEXT,
    feedback JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for resume_scans
ALTER TABLE resume_scans ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can insert their own scans" ON resume_scans FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view their own scans" ON resume_scans FOR SELECT USING (auth.uid() = user_id);


-- Create missing 'interviews' table (used by Dashboard Interview Score)
CREATE TABLE IF NOT EXISTS interviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    average_score INT,
    questions JSONB,
    transcript TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for interviews
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can insert their own interviews" ON interviews FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can view their own interviews" ON interviews FOR SELECT USING (auth.uid() = user_id);
