#!/usr/bin/env python3
"""
Database Cleanup Script - Remove Low Coverage Columns

This script removes columns with less than 20% data coverage from fact_game_metrics.

Columns to be REMOVED (low coverage <20%):
- is_free (12.8%)
- has_discount (12.1%)
- discount_percentage (12.1%)
- avg_hours_2weeks (4.4%)
- median_hours_2weeks (4.4%)
- score_rank (0.1%)
- recommendations (6.0%)
- metacritic_score (2.3%)
- platform_windows (17.5%)
- platform_mac (3.9%)
- platform_linux (2.8%)
- dlc_count (3.9%)
- achievement_count (10.5%)
- language_count (17.5%)
- required_age (0.5%)

Columns being KEPT:
HIGH COVERAGE (90%+):
- appid, name, developer, publisher
- price_category, total_owners
- positive_reviews, total_reviews, rating_percentage, review_category
- genres, top_tags
- created_at, updated_at

MEDIUM COVERAGE (20-90%):
- price_usd, initialprice_usd
- avg_hours_played, median_hours_played
- ccu, hours_per_dollar
- negative_reviews, engagement_score
"""

import psycopg2
from dotenv import load_dotenv
import os
import sys

load_dotenv('/Users/tosdaboss/playintel/backend/.env')
DATABASE_URL = os.getenv("DATABASE_URL")

# Columns to remove (low coverage <20%)
COLUMNS_TO_REMOVE = [
    'is_free',
    'has_discount',
    'discount_percentage',
    'avg_hours_2weeks',
    'median_hours_2weeks',
    'score_rank',
    'recommendations',
    'metacritic_score',
    'platform_windows',
    'platform_mac',
    'platform_linux',
    'dlc_count',
    'achievement_count',
    'language_count',
    'required_age'
]

def show_current_schema():
    """Show current table schema."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'fact_game_metrics'
        ORDER BY ordinal_position
    """)

    columns = cur.fetchall()
    print(f"\nCurrent schema: {len(columns)} columns")
    print("-" * 50)
    for col, dtype in columns:
        status = "🔴 REMOVE" if col in COLUMNS_TO_REMOVE else "✅ KEEP"
        print(f"  {status} {col:<25} ({dtype})")

    conn.close()
    return len(columns)

def remove_columns(dry_run=True):
    """Remove low coverage columns from the table."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("\n" + "=" * 60)
    if dry_run:
        print("DRY RUN - No changes will be made")
    else:
        print("EXECUTING - Columns will be removed!")
    print("=" * 60)

    # Check which columns actually exist
    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'fact_game_metrics'
    """)
    existing_columns = [row[0] for row in cur.fetchall()]

    columns_to_drop = [col for col in COLUMNS_TO_REMOVE if col in existing_columns]
    columns_not_found = [col for col in COLUMNS_TO_REMOVE if col not in existing_columns]

    if columns_not_found:
        print(f"\n⚠️  Columns not found (already removed?): {columns_not_found}")

    print(f"\n📋 Columns to remove: {len(columns_to_drop)}")
    for col in columns_to_drop:
        print(f"   - {col}")

    if not columns_to_drop:
        print("\n✅ No columns to remove!")
        conn.close()
        return

    if dry_run:
        print("\n💡 Run with --execute to actually remove these columns")
        conn.close()
        return

    # Actually remove the columns
    print("\n🔄 Removing columns...")

    for col in columns_to_drop:
        try:
            cur.execute(f"ALTER TABLE fact_game_metrics DROP COLUMN IF EXISTS {col}")
            print(f"   ✅ Removed: {col}")
        except Exception as e:
            print(f"   ❌ Error removing {col}: {e}")
            conn.rollback()

    conn.commit()
    conn.close()

    print("\n✅ Column removal complete!")

def show_final_schema():
    """Show final table schema after cleanup."""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'fact_game_metrics'
        ORDER BY ordinal_position
    """)

    columns = cur.fetchall()

    print("\n" + "=" * 60)
    print(f"FINAL SCHEMA: {len(columns)} columns")
    print("=" * 60)

    print("\n🟢 HIGH COVERAGE (90%+):")
    high = ['appid', 'name', 'developer', 'publisher', 'price_category',
            'total_owners', 'positive_reviews', 'total_reviews',
            'rating_percentage', 'review_category', 'genres', 'top_tags',
            'created_at', 'updated_at']
    for col, dtype in columns:
        if col in high:
            print(f"   {col:<25} ({dtype})")

    print("\n🟡 MEDIUM COVERAGE (20-90%):")
    medium = ['price_usd', 'initialprice_usd', 'avg_hours_played',
              'median_hours_played', 'ccu', 'hours_per_dollar',
              'negative_reviews', 'engagement_score']
    for col, dtype in columns:
        if col in medium:
            print(f"   {col:<25} ({dtype})")

    conn.close()
    return len(columns)

def main():
    print("=" * 60)
    print("PlayIntel Database Cleanup - Remove Low Coverage Columns")
    print("=" * 60)

    # Show current state
    before_count = show_current_schema()

    # Check for --execute flag
    execute = '--execute' in sys.argv

    # Remove columns
    remove_columns(dry_run=not execute)

    if execute:
        # Show final state
        after_count = show_final_schema()
        print(f"\n📊 Summary: {before_count} columns → {after_count} columns")
        print(f"   Removed: {before_count - after_count} low coverage columns")

if __name__ == "__main__":
    main()
