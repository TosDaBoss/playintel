#!/usr/bin/env python3
"""
Rebuild summary_stats and every agg_* table from fact_game_metrics.

Runs as the last step of daily_refresh.py, or on its own:
    python aggregates.py

Rows are replaced with DELETE + INSERT inside one transaction, never DROP or
TRUNCATE, so readers (the API, the MCP server) keep their grants and never see
an empty table. Logic matches create_aggregate_tables.sql and
populate_aggregate_tables.py, done in SQL instead of Python.
"""

import os
import sys
import time

import psycopg

# Tags and genres are comma-separated strings in fact_game_metrics
_TAGS = """
    SELECT left(btrim(t), 100) AS tag, COALESCE(f.total_owners, 0) AS owners,
           f.rating_percentage AS rating, f.price_usd AS price, f.price_category
    FROM fact_game_metrics f, unnest(string_to_array(f.top_tags, ',')) AS t
    WHERE f.top_tags <> '' AND btrim(t) <> ''
"""
_GENRES = _TAGS.replace("f.top_tags", "f.genres")

_NICHE_STATS = """
    SELECT {key}, COUNT(*), TRUNC(AVG(owners))::bigint,
           PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY owners),
           ROUND(AVG(rating)::numeric, 2), ROUND(AVG(price)::numeric, 2),
           COUNT(*) FILTER (WHERE rating >= 90), COUNT(*) FILTER (WHERE owners >= 1000000),
           ROUND(100.0 * COUNT(*) FILTER (WHERE owners >= 100000) / COUNT(*), 2), NOW()
    FROM ({source}) s GROUP BY 1 HAVING COUNT(*) >= 10
"""
_NICHE_PRICE = """
    SELECT {key}, price_category, COUNT(*), TRUNC(AVG(owners))::bigint,
           ROUND(AVG(rating)::numeric, 2),
           ROUND(100.0 * COUNT(*) FILTER (WHERE owners >= 100000) / COUNT(*), 2), NOW()
    FROM ({source}) s WHERE price_category IS NOT NULL GROUP BY 1, 2 HAVING COUNT(*) >= 5
"""

# table -> (columns, SELECT producing them)
AGGREGATES = {
    "summary_stats": (
        "category, total_games, free_games, paid_games, total_owners, avg_playtime_hours,"
        " avg_price_paid_games, avg_rating, total_reviews_submitted, unique_developers, unique_publishers",
        """
        SELECT 'Overall', COUNT(*), COUNT(*) FILTER (WHERE price_usd = 0),
               -- Playtime counts games without SteamSpy playtime as 0; rating needs 10+ reviews
               COUNT(*) FILTER (WHERE price_usd > 0), SUM(total_owners), AVG(COALESCE(avg_hours_played, 0)),
               AVG(price_usd) FILTER (WHERE price_usd > 0),
               AVG(rating_percentage) FILTER (WHERE total_reviews >= 10),
               SUM(total_reviews), COUNT(DISTINCT developer), COUNT(DISTINCT publisher)
        FROM fact_game_metrics
        """,
    ),
    "agg_price_tier_stats": (
        "price_category, sort_order, game_count, avg_owners, median_owners, avg_rating,"
        " avg_playtime_hours, avg_hours_per_dollar, games_90plus_rating, games_1m_plus_owners,"
        " success_rate_100k, updated_at",
        """
        SELECT price_category,
               CASE price_category
                   WHEN 'Free' THEN 1 WHEN 'Budget ($0-$5)' THEN 2 WHEN 'Low ($5-$10)' THEN 3
                   WHEN 'Medium ($10-$20)' THEN 4 WHEN 'Standard ($20-$30)' THEN 5
                   WHEN 'Premium ($30-$50)' THEN 6 WHEN 'AAA ($50+)' THEN 7
               END,
               COUNT(*), ROUND(AVG(total_owners)),
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_owners)::bigint,
               ROUND(AVG(rating_percentage)::numeric, 2), ROUND(AVG(avg_hours_played)::numeric, 2),
               ROUND(AVG(hours_per_dollar)::numeric, 2),
               COUNT(*) FILTER (WHERE rating_percentage >= 90),
               COUNT(*) FILTER (WHERE total_owners >= 1000000),
               ROUND(COUNT(*) FILTER (WHERE total_owners >= 100000)::decimal / COUNT(*) * 100, 2), NOW()
        FROM fact_game_metrics WHERE price_category IS NOT NULL GROUP BY price_category
        """,
    ),
    "agg_ownership_tier_stats": (
        "ownership_tier, sort_order, min_owners, max_owners, game_count, avg_rating, avg_price,"
        " avg_playtime, pct_of_total, updated_at",
        """
        SELECT CASE WHEN total_owners >= 10000000 THEN 'Mega (10M+)'
                    WHEN total_owners >= 1000000 THEN 'Hit (1M-10M)'
                    WHEN total_owners >= 100000 THEN 'Success (100K-1M)'
                    WHEN total_owners >= 10000 THEN 'Moderate (10K-100K)'
                    ELSE 'Small (<10K)' END,
               CASE WHEN total_owners >= 10000000 THEN 1 WHEN total_owners >= 1000000 THEN 2
                    WHEN total_owners >= 100000 THEN 3 WHEN total_owners >= 10000 THEN 4 ELSE 5 END,
               MIN(total_owners), MAX(total_owners), COUNT(*),
               ROUND(AVG(rating_percentage)::numeric, 2), ROUND(AVG(price_usd)::numeric, 2),
               ROUND(AVG(avg_hours_played)::numeric, 2),
               ROUND(COUNT(*)::decimal / (SELECT COUNT(*) FROM fact_game_metrics) * 100, 2), NOW()
        FROM fact_game_metrics GROUP BY 1, 2
        """,
    ),
    "agg_review_tier_stats": (
        "review_category, sort_order, min_rating, max_rating, game_count, avg_owners, avg_reviews,"
        " avg_price, updated_at",
        """
        SELECT review_category,
               CASE review_category
                   WHEN 'Overwhelmingly Positive' THEN 1 WHEN 'Very Positive' THEN 2
                   WHEN 'Mostly Positive' THEN 3 WHEN 'Mixed' THEN 4 WHEN 'Mostly Negative' THEN 5
                   WHEN 'Negative' THEN 6 WHEN 'Overwhelmingly Negative' THEN 7
                   WHEN 'Insufficient Reviews' THEN 8 ELSE 9
               END,
               MIN(rating_percentage), MAX(rating_percentage), COUNT(*), ROUND(AVG(total_owners)),
               ROUND(AVG(total_reviews)), ROUND(AVG(price_usd)::numeric, 2), NOW()
        FROM fact_game_metrics WHERE review_category IS NOT NULL GROUP BY review_category
        """,
    ),
    "agg_developer_stats": (
        "developer, game_count, total_owners, avg_owners_per_game, avg_rating, best_game_name,"
        " best_game_owners, primary_genres, updated_at",
        """
        WITH best AS (
            SELECT DISTINCT ON (developer) developer, name, total_owners
            FROM fact_game_metrics WHERE developer IS NOT NULL AND developer <> ''
            ORDER BY developer, total_owners DESC
        )
        SELECT f.developer, COUNT(*), SUM(f.total_owners), ROUND(AVG(f.total_owners)),
               ROUND(AVG(f.rating_percentage)::numeric, 2), b.name, b.total_owners,
               MODE() WITHIN GROUP (ORDER BY f.genres), NOW()
        FROM fact_game_metrics f JOIN best b ON f.developer = b.developer
        GROUP BY f.developer, b.name, b.total_owners HAVING COUNT(*) >= 3
        """,
    ),
    "agg_tag_stats": (
        "tag, game_count, avg_owners, median_owners, avg_rating, avg_price, games_90plus_rating,"
        " games_1m_plus_owners, success_rate_100k, updated_at",
        _NICHE_STATS.format(key="tag", source=_TAGS),
    ),
    "agg_genre_stats": (
        "genre, game_count, avg_owners, median_owners, avg_rating, avg_price, games_90plus_rating,"
        " games_1m_plus_owners, success_rate_100k, updated_at",
        _NICHE_STATS.format(key="tag", source=_GENRES),
    ),
    "agg_tag_price_matrix": (
        "tag, price_category, game_count, avg_owners, avg_rating, success_rate_100k, updated_at",
        _NICHE_PRICE.format(key="tag", source=_TAGS),
    ),
    "agg_genre_price_performance": (
        "genre, price_category, game_count, avg_owners, avg_rating, success_rate_100k, updated_at",
        _NICHE_PRICE.format(key="tag", source=_GENRES),
    ),
}


def refresh_aggregates(conn, log=print):
    """Rebuild every table in AGGREGATES and record it in agg_refresh_log, in one transaction."""
    with conn.transaction(), conn.cursor() as cur:
        for table, (columns, select) in AGGREGATES.items():
            start = time.time()
            cur.execute(f"DELETE FROM {table}")
            cur.execute(f"INSERT INTO {table} ({columns}) {select}")
            rows, elapsed = cur.rowcount, round(time.time() - start, 2)
            # Production's agg_refresh_log has no unique key on table_name, so no ON CONFLICT
            cur.execute("DELETE FROM agg_refresh_log WHERE table_name = %s", (table,))
            cur.execute("""
                INSERT INTO agg_refresh_log (table_name, last_refreshed, row_count, refresh_duration_seconds)
                VALUES (%s, NOW(), %s, %s)
            """, (table, rows, elapsed))
            log(f"  {table}: {rows} rows in {elapsed}s")


if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        sys.exit("DATABASE_URL environment variable not set")
    with psycopg.connect(db_url) as conn:
        refresh_aggregates(conn)
