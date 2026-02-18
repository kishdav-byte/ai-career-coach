
-- 1. Create the new standardized credit columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_interview INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_resume INT DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS credits_cover INT DEFAULT 0;

-- 2. Migrate data from legacy columns into new columns (Summing them up)
UPDATE users SET 
  credits_interview = COALESCE(interview_credits, 0) + COALESCE(credits_interview_sim, 0),
  credits_resume = COALESCE(rewrite_credits, 0) + COALESCE(resume_credits, 0),
  credits_cover = COALESCE(credits_cover_letter, 0) + COALESCE(strategy_cover_credits, 0) + COALESCE(credits_cover, 0);

-- 3. Sync follow-up naming if shadow columns exist
UPDATE users SET 
  credits_followup = COALESCE(credits_followup, 0) + COALESCE(strategy_followup_credits, 0);

-- 4. [OPTIONAL] Drop the old columns once you verify the dashboard is working
-- DO NOT RUN THESE UNTIL YOU ARE SURE DATA IS MOVED:
-- ALTER TABLE users DROP COLUMN interview_credits;
-- ALTER TABLE users DROP COLUMN credits_interview_sim;
-- ALTER TABLE users DROP COLUMN rewrite_credits;
-- ALTER TABLE users DROP COLUMN resume_credits;
-- ALTER TABLE users DROP COLUMN credits_cover_letter;
-- ALTER TABLE users DROP COLUMN strategy_cover_credits;
-- ALTER TABLE users DROP COLUMN strategy_followup_credits;
