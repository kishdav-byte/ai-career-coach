-- Create a table for administrative settings
CREATE TABLE IF NOT EXISTS admin_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Initialize default notification settings
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
ON CONFLICT (key) DO NOTHING;

-- Grant access to service role
GRANT ALL ON admin_settings TO service_role;
GRANT SELECT ON admin_settings TO authenticated;
