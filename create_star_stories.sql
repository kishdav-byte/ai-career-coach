-- 1. Create the Table
CREATE TABLE IF NOT EXISTS star_stories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    input_text TEXT,
    situation TEXT,
    task TEXT,
    action TEXT,
    result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- 2. Enable RLS
ALTER TABLE star_stories ENABLE ROW LEVEL SECURITY;

-- 3. Create Policies
CREATE POLICY "Users can view their own STAR stories"
ON star_stories FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own STAR stories"
ON star_stories FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own STAR stories"
ON star_stories FOR DELETE
USING (auth.uid() = user_id);
