-- Create waitlist_log table
CREATE TABLE IF NOT EXISTS waitlist_log (
    email TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    project TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_waitlist_created_at ON waitlist_log(created_at DESC);

-- Enable Row Level Security (optional but recommended)
ALTER TABLE waitlist_log ENABLE ROW LEVEL SECURITY;

-- Allow inserts from anyone (for the public form)
CREATE POLICY "Allow public inserts" ON waitlist_log
    FOR INSERT
    WITH CHECK (true);

-- Only allow service role to read (admin only)
CREATE POLICY "Allow service role to read" ON waitlist_log
    FOR SELECT
    USING (auth.role() = 'service_role');
