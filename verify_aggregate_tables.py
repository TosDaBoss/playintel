#!/usr/bin/env python3
"""
Verify Aggregate Tables for PlayIntel

This script checks that all aggregate tables exist and have data.
Run this after populate_aggregate_tables.py to confirm everything is set up.
"""

import psycopg2
from dotenv import load_dotenv
import os

load_dotenv('/Users/tosdaboss/playintel/backend/.env')
DATABASE_URL = os.getenv("DATABASE_URL")

EXPECTED_TABLES = [
    ('agg_price_tier_stats', 7),
    ('agg_tag_stats', 400),  # ~440 tags
    ('agg_genre_stats', 25),  # ~28 genres
    ('agg_ownership_tier_stats', 4),  # 4-5 tiers
    ('agg_review_tier_stats', 7),
    ('agg_tag_price_matrix', 2000),  # ~2,436 combinations
    ('agg_genre_price_performance', 150),  # ~169 combinations
    ('agg_developer_stats', 4000),  # ~4,457 developers
    ('agg_refresh_log', 4),
]

def verify_tables():
    """Verify all aggregate tables exist and have data."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("=" * 70)
    print("PlayIntel Aggregate Tables Verification")
    print("=" * 70)

    all_good = True

    for table_name, min_expected_rows in EXPECTED_TABLES:
        cur.execute(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = '{table_name}'
            )
        """)
        exists = cur.fetchone()[0]

        if not exists:
            print(f"  {table_name:<35} MISSING")
            all_good = False
            continue

        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cur.fetchone()[0]

        if row_count >= min_expected_rows:
            status = "OK"
        elif row_count > 0:
            status = "LOW"
            all_good = False
        else:
            status = "EMPTY"
            all_good = False

        print(f"  {table_name:<35} {row_count:>8,} rows  [{status}]")

    print("=" * 70)

    # Check refresh log for last update times
    cur.execute("""
        SELECT table_name, last_refreshed, row_count
        FROM agg_refresh_log
        ORDER BY last_refreshed DESC
    """)
    refresh_data = cur.fetchall()

    if refresh_data:
        print("\nLast Refresh Times:")
        print("-" * 70)
        for table, refreshed, count in refresh_data:
            print(f"  {table:<35} {str(refreshed)[:19]}  ({count:,} rows)")

    print("=" * 70)

    if all_good:
        print("\nAll aggregate tables are ready for PlayIntel!")
    else:
        print("\nSome tables need attention. Run populate_aggregate_tables.py")

    conn.close()
    return all_good


def show_sample_data():
    """Show sample data from each aggregate table."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("\n" + "=" * 70)
    print("SAMPLE DATA FROM AGGREGATE TABLES")
    print("=" * 70)

    # Price tier stats
    print("\nagg_price_tier_stats (Price Strategy):")
    cur.execute("""
        SELECT price_category, game_count, avg_owners, avg_rating, success_rate_100k
        FROM agg_price_tier_stats
        ORDER BY sort_order
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<25} {row[1]:>6} games, {row[2]:>10,} avg owners, {row[3]}% rating, {row[4]}% success")

    # Top tags
    print("\nagg_tag_stats (Top 5 Tags by Game Count):")
    cur.execute("""
        SELECT tag, game_count, avg_owners, avg_rating
        FROM agg_tag_stats
        ORDER BY game_count DESC
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<25} {row[1]:>6} games, {row[2]:>10,} avg owners, {row[3]}% rating")

    # Ownership tiers
    print("\nagg_ownership_tier_stats (Success Benchmarks):")
    cur.execute("""
        SELECT ownership_tier, game_count, pct_of_total, avg_rating
        FROM agg_ownership_tier_stats
        ORDER BY sort_order
    """)
    for row in cur.fetchall():
        print(f"  {row[0]:<25} {row[1]:>6} games ({row[2]}% of total), {row[3]}% rating")

    conn.close()


if __name__ == "__main__":
    verify_tables()
    show_sample_data()
