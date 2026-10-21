-- Read-only role for the PlayIntel API and MCP server.
-- Run once in the Supabase SQL editor (as postgres). Replace the password first.
--
-- Why: /api/chat and the MCP run_sql tool execute model-written SQL. A read-only
-- transaction blocks INSERT/UPDATE/DELETE but still allows side-effect functions
-- (e.g. pg_terminate_backend). A role that can only SELECT a fixed list of tables,
-- and cannot see users/waitlist at all, is the real boundary.

CREATE ROLE playintel_reader LOGIN PASSWORD 'CHANGE_ME_long_random_password'
    NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT;

ALTER ROLE playintel_reader SET default_transaction_read_only = on;
ALTER ROLE playintel_reader SET statement_timeout = '15s';
ALTER ROLE playintel_reader SET idle_in_transaction_session_timeout = '30s';
ALTER ROLE playintel_reader CONNECTION LIMIT 20;

GRANT CONNECT ON DATABASE postgres TO playintel_reader;
GRANT USAGE ON SCHEMA public TO playintel_reader;

-- Analytics tables only. Deliberately NOT granted: users, waitlist, steam_apps.
GRANT SELECT ON
    fact_game_metrics,
    summary_stats,
    dim_developers,
    dim_publishers,
    agg_price_tier_stats,
    agg_tag_stats,
    agg_genre_stats,
    agg_ownership_tier_stats,
    agg_review_tier_stats,
    agg_tag_price_matrix,
    agg_genre_price_performance,
    agg_developer_stats,
    agg_refresh_log
TO playintel_reader;

-- If Row Level Security is enabled on any of the tables above, the role sees
-- zero rows until it has a policy. Check with:
--   SELECT relname FROM pg_class WHERE relrowsecurity AND relnamespace = 'public'::regnamespace;
-- and for each analytics table listed, add:
--   CREATE POLICY reader_all ON <table> FOR SELECT TO playintel_reader USING (true);

-- Connection string (Supabase pooler expects user.<project-ref>):
--   postgresql://playintel_reader.<project-ref>:<password>@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
-- Use it as DATABASE_URL for the backend and MCP server. Keep the postgres
-- superuser URL only for the ETL (GitHub Actions secret).
