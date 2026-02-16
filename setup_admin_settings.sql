-- Refined Setup for Administrative Settings
-- Using gen_random_uuid() for better compatibility with modern Postgres

CREATE TABLE IF NOT EXISTS admin_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Initialize default notification settings if they don't exist
INSERT INTO admin_settings (key, value)
VALUES (
    'notification_settings',
    '{
        "phone_number": "8649099115",
        "carrier_gateway": "vtext.com",
        "notify_on_signup": true,
        "notify_on_complaint": true
    }'::jsonb
)
ON CONFLICT (key) DO UPDATE 
SET value = EXCLUDED.value, 
    updated_at = now();

-- Ensure service role and internal users can access it
GRANT ALL ON admin_settings TO service_role;
GRANT SELECT ON admin_settings TO authenticated;
GRANT SELECT ON admin_settings TO anon;
