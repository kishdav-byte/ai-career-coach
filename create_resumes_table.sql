-- Create 'resumes' table for comprehensive resume history tracking
CREATE TABLE IF NOT EXISTS public.resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    overall_score INTEGER,
    job_title TEXT,
    company_name TEXT,
    version_type TEXT DEFAULT 'analysis', -- 'analysis', 'rewrite', 'optimization'
    resume_text TEXT,
    content JSONB, -- Store full analysis results
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.resumes ENABLE ROW LEVEL SECURITY;

-- Create Policies
CREATE POLICY "Users can view their own resumes"
ON public.resumes FOR SELECT
USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own resumes"
ON public.resumes FOR INSERT
WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own resumes"
ON public.resumes FOR UPDATE
USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own resumes"
ON public.resumes FOR DELETE
USING (auth.uid() = user_id);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON public.resumes(user_id);
CREATE INDEX IF NOT EXISTS idx_resumes_created_at ON public.resumes(created_at DESC);
