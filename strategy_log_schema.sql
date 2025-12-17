-- Create Job Tracking Table
create table public.user_jobs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  job_title text not null,
  company_name text not null,
  job_description text, -- Optional: store the JD for quick reference
  status text default 'Identified', -- Options: Identified, Applied, Interviewing, Offer, Closed
  resume_score int default 0, -- Auto-update from Resume Diagnosis
  interview_score int default 0, -- Auto-update from Interview Lab
  created_at timestamp with time zone default now()
);

-- Enable RLS (Row Level Security)
alter table public.user_jobs enable row level security;

-- Policy: Users can only see their own jobs
create policy "Users can only see their own jobs" on public.user_jobs
  for all using (auth.uid() = user_id);

-- Grant access to authenticated users
grant all on table public.user_jobs to authenticated;
grant all on table public.user_jobs to service_role;
