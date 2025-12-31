ALTER TABLE star_stories ADD COLUMN IF NOT EXISTS title TEXT;
-- Backfill existing records with a default title if needed, or leave null
UPDATE star_stories SET title = 'Strategic Story ' || substring(id::text, 1, 4) WHERE title IS NULL;
