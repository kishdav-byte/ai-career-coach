-- Track Free Resume Diagnoses
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS analysis_count INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_analysis_date TIMESTAMP WITH TIME ZONE;

-- Track Free Role Reversal Sessions
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS role_reversal_count INT DEFAULT 0;

-- (Optional) Track Free Lab Assistant Usage if needed later
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS lab_assistant_count INT DEFAULT 0;

-- Track Strategy Lab Credits (Required for Cover Letter & Tools)
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS credits_negotiation INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS credits_inquisitor INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS credits_followup INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS credits_30_60_90 INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS credits_cover_letter INT DEFAULT 0,
ADD COLUMN IF NOT EXISTS credits_interview_sim INT DEFAULT 0;
