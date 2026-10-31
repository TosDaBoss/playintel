-- Restore missing keys and add the history (snapshot) tables.
-- Run once in the Supabase SQL editor (as postgres), BEFORE merging the
-- matching code. Safe to re-run: every step checks whether it is already done.
--
-- Why the keys: production lost every primary key, so daily_refresh.py's
-- INSERT ... ON CONFLICT (appid) for new games fails and no new games are saved.
-- The keys also give each table an index on appid.
--
-- Why the snapshots: each refresh overwrites a game's numbers, so there is no
-- history. daily_refresh.py now copies them into these tables once a month
-- (all games) and once a week (games first seen in the last year), for
-- month-on-month and year-on-year comparisons and, later, model training.

BEGIN;

-- 1. Stop if steam_apps has duplicate or missing game IDs (a key can't be added)
DO $$
DECLARE dupes int; nulls int;
BEGIN
    SELECT count(*) INTO dupes FROM (
        SELECT appid FROM steam_apps GROUP BY appid HAVING count(*) > 1) d;
    SELECT count(*) INTO nulls FROM steam_apps WHERE appid IS NULL;
    IF dupes > 0 OR nulls > 0 THEN
        RAISE EXCEPTION 'steam_apps has % duplicated and % missing appids; nothing was changed', dupes, nulls;
    END IF;
END $$;

-- 2. Primary keys the ETL relies on
DO $$
DECLARE t text; col text;
BEGIN
    FOR t, col IN VALUES ('steam_apps', 'appid'), ('fact_game_metrics', 'appid'),
                         ('agg_refresh_log', 'table_name')
    LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_constraint
                       WHERE conrelid = t::regclass AND contype = 'p') THEN
            EXECUTE format('ALTER TABLE %I ADD PRIMARY KEY (%I)', t, col);
        END IF;
    END LOOP;
END $$;

-- 3. Monthly snapshot of every game (snapshot_month = 1st of the month)
CREATE TABLE IF NOT EXISTS game_snapshots_monthly (
    snapshot_month      date NOT NULL,
    appid               integer NOT NULL,
    name                text,
    developer           text,
    publisher           text,
    price_usd           numeric,
    initialprice_usd    numeric,
    price_category      text,
    total_owners        integer,
    positive_reviews    integer,
    negative_reviews    integer,
    total_reviews       integer,
    rating_percentage   numeric,
    avg_hours_played    numeric,
    median_hours_played numeric,
    ccu                 integer,
    genres              text,
    top_tags            text,
    first_seen          timestamp,   -- when the pipeline first found the game
    data_as_of          timestamp,   -- when SteamSpy last refreshed this game
    PRIMARY KEY (snapshot_month, appid)
);
CREATE INDEX IF NOT EXISTS game_snapshots_monthly_appid ON game_snapshots_monthly (appid);

-- 4. Weekly snapshot of recent games (snapshot_week = Monday), same columns
CREATE TABLE IF NOT EXISTS game_snapshots_weekly (
    LIKE game_snapshots_monthly INCLUDING DEFAULTS
);
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_name = 'game_snapshots_weekly' AND column_name = 'snapshot_month') THEN
        ALTER TABLE game_snapshots_weekly RENAME COLUMN snapshot_month TO snapshot_week;
        ALTER TABLE game_snapshots_weekly ADD PRIMARY KEY (snapshot_week, appid);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS game_snapshots_weekly_appid ON game_snapshots_weekly (appid);

-- 5. Monthly copy of the market stats (overall, price tiers, tags, genres)
CREATE TABLE IF NOT EXISTS market_snapshots_monthly (
    snapshot_month    date NOT NULL,
    dimension         text NOT NULL,   -- 'market', 'price_tier', 'tag' or 'genre'
    key               text NOT NULL,   -- 'all', the price category, tag or genre
    game_count        integer,
    avg_owners        bigint,
    median_owners     bigint,
    avg_rating        numeric,
    avg_price         numeric,
    success_rate_100k numeric,
    PRIMARY KEY (snapshot_month, dimension, key)
);

-- 6. Read access for the API and MCP server, and nobody else. Supabase exposes
--    public tables through its REST API, so RLS keeps the anon key out; the
--    postgres owner (the ETL) is not affected by RLS.
DO $$
DECLARE t text;
BEGIN
    FOREACH t IN ARRAY ARRAY['game_snapshots_monthly', 'game_snapshots_weekly', 'market_snapshots_monthly']
    LOOP
        EXECUTE format('GRANT SELECT ON %I TO playintel_reader', t);
        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', t);
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE tablename = t AND policyname = 'reader_all') THEN
            EXECUTE format('CREATE POLICY reader_all ON %I FOR SELECT TO playintel_reader USING (true)', t);
        END IF;
    END LOOP;
END $$;

COMMIT;

-- Check (should list 3 keys and 3 snapshot tables):
-- SELECT conrelid::regclass, conname FROM pg_constraint
--  WHERE contype = 'p' AND conrelid::regclass::text IN ('steam_apps', 'fact_game_metrics', 'agg_refresh_log');
-- SELECT tablename FROM pg_tables WHERE tablename LIKE '%snapshots%';
