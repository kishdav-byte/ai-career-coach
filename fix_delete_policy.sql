-- Enable RLS on interviews table
ALTER TABLE interviews ENABLE ROW LEVEL SECURITY;

-- POLICY: Allow users to DELETE their own interviews
-- This ensures that a user can only remove rows where the user_id matches their authenticated ID.
DROP POLICY IF EXISTS "Users can delete their own interviews" ON interviews;

CREATE POLICY "Users can delete their own interviews"
ON interviews
FOR DELETE
USING (auth.uid() = user_id);
