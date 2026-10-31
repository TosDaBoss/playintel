#!/usr/bin/env python3
"""
Keep history: copy each game's numbers and the market stats into snapshot tables.

The refresh overwrites steam_apps and the agg_* tables, so without this there is
nothing to compare against. Runs after refresh_aggregates in daily_refresh.py,
or on its own:
    python snapshots.py

- game_snapshots_monthly:   every game, once per calendar month
- game_snapshots_weekly:    games first seen in the last year, once per week (Monday)
- market_snapshots_monthly: overall, price tier, tag and genre stats, once per month

The first successful run of each month/week takes the snapshot; later runs in the
same period only add games that weren't in it yet (ON CONFLICT DO NOTHING), so a
failed 1st-of-month run is picked up the next day. Tables come from
add_keys_and_snapshots.sql.
"""

import os
import sys

import psycopg

_GAME_COLUMNS = """
    appid, name, developer, publisher, price_usd, initialprice_usd, price_category,
    total_owners, positive_reviews, negative_reviews, total_reviews, rating_percentage,
    avg_hours_played, median_hours_played, ccu, genres, top_tags, first_seen, data_as_of
"""
# data_as_of comes from steam_apps: fact_game_metrics.updated_at is the rebuild time
_GAME_SELECT = """
    SELECT {period}, f.appid, f.name, f.developer, f.publisher, f.price_usd, f.initialprice_usd,
           f.price_category, f.total_owners, f.positive_reviews, f.negative_reviews,
           f.total_reviews, f.rating_percentage, f.avg_hours_played, f.median_hours_played,
           f.ccu, f.genres, f.top_tags, s.created_at, s.updated_at
    FROM fact_game_metrics f JOIN steam_apps s USING (appid)
"""
_MONTH = "date_trunc('month', NOW())::date"
_WEEK = "date_trunc('week', NOW())::date"

SNAPSHOTS = {
    "game_snapshots_monthly": (
        f"snapshot_month, {_GAME_COLUMNS}",
        _GAME_SELECT.format(period=_MONTH),
    ),
    "game_snapshots_weekly": (
        f"snapshot_week, {_GAME_COLUMNS}",
        _GAME_SELECT.format(period=_WEEK) + " WHERE s.created_at >= NOW() - INTERVAL '1 year'",
    ),
    "market_snapshots_monthly": (
        "snapshot_month, dimension, key, game_count, avg_owners, median_owners, avg_rating,"
        " avg_price, success_rate_100k",
        f"""
        SELECT {_MONTH}, 'market', 'all', s.total_games, s.total_owners / NULLIF(s.total_games, 0),
               p.median_owners, s.avg_rating, s.avg_price_paid_games, p.success_rate_100k
        FROM summary_stats s,
             (SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY COALESCE(total_owners, 0)) AS median_owners,
                     ROUND(100.0 * COUNT(*) FILTER (WHERE total_owners >= 100000) / NULLIF(COUNT(*), 0), 2)
                         AS success_rate_100k
              FROM fact_game_metrics) p
        UNION ALL
        SELECT {_MONTH}, 'price_tier', price_category, game_count, avg_owners, median_owners,
               avg_rating, NULL, success_rate_100k FROM agg_price_tier_stats
        UNION ALL
        SELECT {_MONTH}, 'tag', tag, game_count, avg_owners, median_owners, avg_rating, avg_price,
               success_rate_100k FROM agg_tag_stats
        UNION ALL
        SELECT {_MONTH}, 'genre', genre, game_count, avg_owners, median_owners, avg_rating, avg_price,
               success_rate_100k FROM agg_genre_stats
        """,
    ),
}


def take_snapshots(conn, log=print):
    """Add this month's/week's rows to each table in SNAPSHOTS if they aren't there yet."""
    with conn.cursor() as cur:
        cur.execute("SELECT to_regclass('game_snapshots_monthly')")
        if cur.fetchone()[0] is None:
            log("  Snapshot tables missing: run add_keys_and_snapshots.sql in Supabase. Skipped.")
            return
    with conn.transaction(), conn.cursor() as cur:
        for table, (columns, select) in SNAPSHOTS.items():
            cur.execute(f"INSERT INTO {table} ({columns}) {select} ON CONFLICT DO NOTHING")
            log(f"  {table}: {cur.rowcount} new rows" if cur.rowcount else
                f"  {table}: already taken for this period")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL environment variable not set")
    with psycopg.connect(db_url) as conn:
        take_snapshots(conn)
