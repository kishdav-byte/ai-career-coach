-- Function to decrement generic 'credits'
create or replace function decrement_credits(row_id uuid)
returns void as $$
begin
  update users
  set credits = credits - 1
  where id = row_id AND credits > 0 AND (is_unlimited IS NULL OR is_unlimited = FALSE);
end;
$$ language plpgsql;

-- Function to decrement 'rewrite_credits' (with fallback to generic credits in application layer, 
-- but this function strictly handles the rewrite_credits column)
create or replace function decrement_rewrite_credits(row_id uuid)
returns void as $$
begin
  update users
  set rewrite_credits = rewrite_credits - 1
  where id = row_id AND rewrite_credits > 0;
end;
$$ language plpgsql;
