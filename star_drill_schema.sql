-- Add STAR Drill Tracking
-- Adds a counter for free usage checking and a timestamp for monthly resets

ALTER TABLE users 
ADD COLUMN IF NOT EXISTS star_drill_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS last_star_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Optional: Comment on columns
COMMENT ON COLUMN users.star_drill_count IS 'Tracks usage of STAR Drill for rate limiting free users (Limit: 3/mo)';
