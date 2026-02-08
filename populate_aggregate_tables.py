#!/usr/bin/env python3
"""
Populate Aggregate Tables for PlayIntel

This script creates and populates all aggregate tables including:
- Tag statistics (requires parsing comma-separated tags)
- Genre statistics (requires parsing comma-separated genres)
- Tag + Price matrix
- Genre + Price performance

Run after create_aggregate_tables.sql
"""

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from collections import defaultdict
import os
import time

load_dotenv('/Users/tosdaboss/playintel/backend/.env')
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def populate_tag_stats():
    """Populate agg_tag_stats by parsing top_tags column."""
    print("\n📊 Populating agg_tag_stats...")
    start = time.time()

    conn = get_connection()
    cur = conn.cursor()

    # Fetch all games with tags
    cur.execute("""
        SELECT top_tags, total_owners, rating_percentage, price_usd
        FROM fact_game_metrics
        WHERE top_tags IS NOT NULL AND top_tags <> ''
    """)

    # Aggregate by tag
    tag_data = defaultdict(lambda: {
        'owners': [], 'ratings': [], 'prices': [], 'count': 0
    })

    for row in cur.fetchall():
        tags = [t.strip() for t in row[0].split(',')]
        for tag in tags:
            if tag:
                tag_data[tag]['owners'].append(row[1] or 0)
                if row[2] is not None:
                    tag_data[tag]['ratings'].append(float(row[2]))
                if row[3] is not None:
                    tag_data[tag]['prices'].append(float(row[3]))
                tag_data[tag]['count'] += 1

    # Calculate stats and insert
    cur.execute("DELETE FROM agg_tag_stats")

    rows = []
    for tag, data in tag_data.items():
        if data['count'] >= 10:  # Only tags with 10+ games
            owners = sorted(data['owners'])
            median_owners = owners[len(owners)//2] if owners else 0

            rows.append((
                tag[:100],  # Truncate long tags
                data['count'],
                int(sum(data['owners']) / len(data['owners'])) if data['owners'] else 0,
                median_owners,
                round(sum(data['ratings']) / len(data['ratings']), 2) if data['ratings'] else None,
                round(sum(data['prices']) / len(data['prices']), 2) if data['prices'] else None,
                sum(1 for r in data['ratings'] if r >= 90),
                sum(1 for o in data['owners'] if o >= 1000000),
                round(sum(1 for o in data['owners'] if o >= 100000) / data['count'] * 100, 2)
            ))

    execute_values(cur, """
        INSERT INTO agg_tag_stats
        (tag, game_count, avg_owners, median_owners, avg_rating, avg_price,
         games_90plus_rating, games_1m_plus_owners, success_rate_100k)
        VALUES %s
    """, rows)

    conn.commit()
    elapsed = time.time() - start
    print(f"   ✅ Inserted {len(rows)} tags in {elapsed:.1f}s")

    # Update refresh log
    cur.execute("""
        INSERT INTO agg_refresh_log (table_name, last_refreshed, row_count, refresh_duration_seconds)
        VALUES ('agg_tag_stats', NOW(), %s, %s)
        ON CONFLICT (table_name) DO UPDATE SET
            last_refreshed = NOW(), row_count = %s, refresh_duration_seconds = %s
    """, (len(rows), elapsed, len(rows), elapsed))
    conn.commit()

    conn.close()
    return len(rows)


def populate_genre_stats():
    """Populate agg_genre_stats by parsing genres column."""
    print("\n📊 Populating agg_genre_stats...")
    start = time.time()

    conn = get_connection()
    cur = conn.cursor()

    # Fetch all games with genres
    cur.execute("""
        SELECT genres, total_owners, rating_percentage, price_usd
        FROM fact_game_metrics
        WHERE genres IS NOT NULL AND genres <> ''
    """)

    # Aggregate by genre
    genre_data = defaultdict(lambda: {
        'owners': [], 'ratings': [], 'prices': [], 'count': 0
    })

    for row in cur.fetchall():
        genres = [g.strip() for g in row[0].split(',')]
        for genre in genres:
            if genre:
                genre_data[genre]['owners'].append(row[1] or 0)
                if row[2] is not None:
                    genre_data[genre]['ratings'].append(float(row[2]))
                if row[3] is not None:
                    genre_data[genre]['prices'].append(float(row[3]))
                genre_data[genre]['count'] += 1

    # Calculate stats and insert
    cur.execute("DELETE FROM agg_genre_stats")

    rows = []
    for genre, data in genre_data.items():
        if data['count'] >= 10:  # Only genres with 10+ games
            owners = sorted(data['owners'])
            median_owners = owners[len(owners)//2] if owners else 0

            rows.append((
                genre[:100],
                data['count'],
                int(sum(data['owners']) / len(data['owners'])) if data['owners'] else 0,
                median_owners,
                round(sum(data['ratings']) / len(data['ratings']), 2) if data['ratings'] else None,
                round(sum(data['prices']) / len(data['prices']), 2) if data['prices'] else None,
                sum(1 for r in data['ratings'] if r >= 90),
                sum(1 for o in data['owners'] if o >= 1000000),
                round(sum(1 for o in data['owners'] if o >= 100000) / data['count'] * 100, 2)
            ))

    execute_values(cur, """
        INSERT INTO agg_genre_stats
        (genre, game_count, avg_owners, median_owners, avg_rating, avg_price,
         games_90plus_rating, games_1m_plus_owners, success_rate_100k)
        VALUES %s
    """, rows)

    conn.commit()
    elapsed = time.time() - start
    print(f"   ✅ Inserted {len(rows)} genres in {elapsed:.1f}s")

    cur.execute("""
        INSERT INTO agg_refresh_log (table_name, last_refreshed, row_count, refresh_duration_seconds)
        VALUES ('agg_genre_stats', NOW(), %s, %s)
        ON CONFLICT (table_name) DO UPDATE SET
            last_refreshed = NOW(), row_count = %s, refresh_duration_seconds = %s
    """, (len(rows), elapsed, len(rows), elapsed))
    conn.commit()

    conn.close()
    return len(rows)


def populate_tag_price_matrix():
    """Populate agg_tag_price_matrix for tag + price tier analysis."""
    print("\n📊 Populating agg_tag_price_matrix...")
    start = time.time()

    conn = get_connection()
    cur = conn.cursor()

    # Fetch all games with tags and price category
    cur.execute("""
        SELECT top_tags, price_category, total_owners, rating_percentage
        FROM fact_game_metrics
        WHERE top_tags IS NOT NULL AND top_tags <> ''
          AND price_category IS NOT NULL
    """)

    # Aggregate by tag + price
    matrix_data = defaultdict(lambda: {
        'owners': [], 'ratings': [], 'count': 0
    })

    for row in cur.fetchall():
        tags = [t.strip() for t in row[0].split(',')]
        price_cat = row[1]
        for tag in tags:
            if tag:
                key = (tag, price_cat)
                matrix_data[key]['owners'].append(row[2] or 0)
                if row[3] is not None:
                    matrix_data[key]['ratings'].append(float(row[3]))
                matrix_data[key]['count'] += 1

    # Calculate stats and insert
    cur.execute("DELETE FROM agg_tag_price_matrix")

    rows = []
    for (tag, price_cat), data in matrix_data.items():
        if data['count'] >= 5:  # Only combinations with 5+ games
            rows.append((
                tag[:100],
                price_cat,
                data['count'],
                int(sum(data['owners']) / len(data['owners'])) if data['owners'] else 0,
                round(sum(data['ratings']) / len(data['ratings']), 2) if data['ratings'] else None,
                round(sum(1 for o in data['owners'] if o >= 100000) / data['count'] * 100, 2)
            ))

    execute_values(cur, """
        INSERT INTO agg_tag_price_matrix
        (tag, price_category, game_count, avg_owners, avg_rating, success_rate_100k)
        VALUES %s
    """, rows)

    conn.commit()
    elapsed = time.time() - start
    print(f"   ✅ Inserted {len(rows)} tag+price combinations in {elapsed:.1f}s")

    cur.execute("""
        INSERT INTO agg_refresh_log (table_name, last_refreshed, row_count, refresh_duration_seconds)
        VALUES ('agg_tag_price_matrix', NOW(), %s, %s)
        ON CONFLICT (table_name) DO UPDATE SET
            last_refreshed = NOW(), row_count = %s, refresh_duration_seconds = %s
    """, (len(rows), elapsed, len(rows), elapsed))
    conn.commit()

    conn.close()
    return len(rows)


def populate_genre_price_performance():
    """Populate agg_genre_price_performance for genre + price analysis."""
    print("\n📊 Populating agg_genre_price_performance...")
    start = time.time()

    conn = get_connection()
    cur = conn.cursor()

    # Fetch all games with genres and price category
    cur.execute("""
        SELECT genres, price_category, total_owners, rating_percentage
        FROM fact_game_metrics
        WHERE genres IS NOT NULL AND genres <> ''
          AND price_category IS NOT NULL
    """)

    # Aggregate by genre + price
    matrix_data = defaultdict(lambda: {
        'owners': [], 'ratings': [], 'count': 0
    })

    for row in cur.fetchall():
        genres = [g.strip() for g in row[0].split(',')]
        price_cat = row[1]
        for genre in genres:
            if genre:
                key = (genre, price_cat)
                matrix_data[key]['owners'].append(row[2] or 0)
                if row[3] is not None:
                    matrix_data[key]['ratings'].append(float(row[3]))
                matrix_data[key]['count'] += 1

    # Calculate stats and insert
    cur.execute("DELETE FROM agg_genre_price_performance")

    rows = []
    for (genre, price_cat), data in matrix_data.items():
        if data['count'] >= 5:  # Only combinations with 5+ games
            rows.append((
                genre[:100],
                price_cat,
                data['count'],
                int(sum(data['owners']) / len(data['owners'])) if data['owners'] else 0,
                round(sum(data['ratings']) / len(data['ratings']), 2) if data['ratings'] else None,
                round(sum(1 for o in data['owners'] if o >= 100000) / data['count'] * 100, 2)
            ))

    execute_values(cur, """
        INSERT INTO agg_genre_price_performance
        (genre, price_category, game_count, avg_owners, avg_rating, success_rate_100k)
        VALUES %s
    """, rows)

    conn.commit()
    elapsed = time.time() - start
    print(f"   ✅ Inserted {len(rows)} genre+price combinations in {elapsed:.1f}s")

    cur.execute("""
        INSERT INTO agg_refresh_log (table_name, last_refreshed, row_count, refresh_duration_seconds)
        VALUES ('agg_genre_price_performance', NOW(), %s, %s)
        ON CONFLICT (table_name) DO UPDATE SET
            last_refreshed = NOW(), row_count = %s, refresh_duration_seconds = %s
    """, (len(rows), elapsed, len(rows), elapsed))
    conn.commit()

    conn.close()
    return len(rows)


def show_summary():
    """Show summary of all aggregate tables."""
    conn = get_connection()
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("AGGREGATE TABLES SUMMARY")
    print("=" * 60)

    cur.execute("""
        SELECT table_name, last_refreshed, row_count, refresh_duration_seconds
        FROM agg_refresh_log
        ORDER BY table_name
    """)

    print(f"\n{'Table':<35} {'Rows':>10} {'Last Refresh':>20}")
    print("-" * 70)
    for row in cur.fetchall():
        print(f"{row[0]:<35} {row[1]:>10,} {str(row[2])[:19]:>20}")

    conn.close()


def main():
    print("=" * 60)
    print("PlayIntel Aggregate Tables Population")
    print("=" * 60)

    total_start = time.time()

    # Run the SQL script first
    print("\n📋 Running SQL script for base tables...")
    conn = get_connection()
    cur = conn.cursor()

    with open('/Users/tosdaboss/playintel/create_aggregate_tables.sql', 'r') as f:
        sql = f.read()
        cur.execute(sql)
    conn.commit()
    print("   ✅ Base tables created")
    conn.close()

    # Populate tag and genre tables via Python
    populate_tag_stats()
    populate_genre_stats()
    populate_tag_price_matrix()
    populate_genre_price_performance()

    total_elapsed = time.time() - total_start

    print(f"\n🎉 All tables populated in {total_elapsed:.1f}s")

    show_summary()


if __name__ == "__main__":
    main()
