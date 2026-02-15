-- Create users table for signup data
-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    plan TEXT NOT NULL CHECK (plan IN ('free', 'indie', 'studio')),
    queries_used INTEGER DEFAULT 0,
    query_limit INTEGER DEFAULT 5,
    query_reset_date TIMESTAMP WITH TIME ZONE,

    -- Stripe integration fields
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    subscription_status TEXT CHECK (subscription_status IN ('active', 'canceled', 'past_due', 'trialing', NULL)),

    -- Signup tracking
    signup_source TEXT DEFAULT 'website',
    signup_completed BOOLEAN DEFAULT false,
    stripe_checkout_pending BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_plan ON users(plan);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (for API routes)
CREATE POLICY "Allow service role full access" ON users
    FOR ALL
    USING (auth.role() = 'service_role');

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Optional: Create a view for admin dashboard
CREATE OR REPLACE VIEW users_summary AS
SELECT
    plan,
    COUNT(*) as total_users,
    COUNT(*) FILTER (WHERE signup_completed = true) as completed_signups,
    COUNT(*) FILTER (WHERE stripe_checkout_pending = true) as pending_payments,
    COUNT(*) FILTER (WHERE subscription_status = 'active') as active_subscriptions
FROM users
GROUP BY plan;
