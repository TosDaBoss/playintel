#!/usr/bin/env python3
"""
PlayIntel Daily Data Refresh Script
Designed for cloud execution (GitHub Actions, Railway, etc.)

This script:
1. Fetches new games from SteamSpy
2. Enriches them with SteamSpy + Steam API data
3. Updates analytics/aggregate tables

Environment Variables Required:
- DATABASE_URL: Supabase PostgreSQL connection string

Usage:
    python daily_refresh.py                    # Full refresh
    python daily_refresh.py --fetch-only       # Only fetch new games
    python daily_refresh.py --enrich-only      # Only enrich existing games
    python daily_refresh.py --analytics-only   # Only update analytics
"""

import asyncio
import aiohttp
import psycopg
import os
import sys
import time
import json
import argparse
from datetime import datetime
from typing import List, Dict, Optional, Set

# Configuration
STEAMSPY_API_BASE = "https://steamspy.com/api.php"
STEAM_API_BASE = "https://store.steampowered.com/api/appdetails"

# Rate limits
STEAMSPY_PAGE_DELAY = 61  # seconds between page requests
STEAMSPY_APP_DELAY = 0.25  # seconds between app detail requests
STEAM_API_DELAY = 1.5  # seconds between Steam API requests
CONCURRENT_REQUESTS = 4

# Limits for daily runs (to keep runtime reasonable)
MAX_NEW_GAMES_PER_RUN = 500
MAX_ENRICHMENTS_PER_RUN = 1000  # For new games without data
MAX_UPDATES_PER_RUN = 2000      # For existing games needing refresh
MAX_PAGES_TO_CHECK = 20         # ~20 minutes of page fetching max
REFRESH_OLDER_THAN_DAYS = 7     # Refresh games not updated in X days


def get_db_connection():
    """Get database connection from environment."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return psycopg.connect(db_url)


def log(message: str):
    """Log with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


# ============================================================================
# STEP 1: Fetch New Games from SteamSpy
# ============================================================================

def fetch_new_games(conn) -> int:
    """Fetch new games from SteamSpy that aren't in our database."""
    import requests

    log("=" * 60)
    log("STEP 1: Fetching new games from SteamSpy")
    log("=" * 60)

    # Get existing app IDs
    cursor = conn.cursor()
    cursor.execute("SELECT appid FROM steam_apps;")
    existing_appids = set(row[0] for row in cursor.fetchall())
    cursor.close()

    log(f"Existing games in database: {len(existing_appids):,}")

    new_apps = []
    consecutive_empty = 0

    for page in range(MAX_PAGES_TO_CHECK):
        try:
            url = f"{STEAMSPY_API_BASE}?request=all&page={page}"
            log(f"Fetching page {page}...")

            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()

            if not data:
                log("Reached end of SteamSpy data")
                break

            # Find new games on this page
            page_new = []
            for appid, info in data.items():
                appid_int = int(appid)
                if appid_int not in existing_appids:
                    page_new.append({
                        'appid': appid_int,
                        'name': info.get('name', 'Unknown')
                    })
                    existing_appids.add(appid_int)

            if page_new:
                new_apps.extend(page_new)
                log(f"  Found {len(page_new)} new games (total: {len(new_apps)})")
                consecutive_empty = 0
            else:
                log(f"  No new games on this page")
                consecutive_empty += 1
                if consecutive_empty >= 3:
                    log("3 consecutive empty pages, stopping search")
                    break

            # Check if we've hit our limit
            if len(new_apps) >= MAX_NEW_GAMES_PER_RUN:
                log(f"Reached limit of {MAX_NEW_GAMES_PER_RUN} new games")
                break

            # Rate limit
            if page < MAX_PAGES_TO_CHECK - 1:
                time.sleep(STEAMSPY_PAGE_DELAY)

        except Exception as e:
            log(f"Error on page {page}: {e}")
            break

    # Insert new games
    if new_apps:
        log(f"Inserting {len(new_apps)} new games...")
        cursor = conn.cursor()
        now = datetime.now()

        cursor.executemany(
            """
            INSERT INTO steam_apps (appid, name, created_at, updated_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (appid) DO UPDATE SET
                name = EXCLUDED.name,
                updated_at = EXCLUDED.updated_at
            """,
            [(app['appid'], app['name'], now, now) for app in new_apps]
        )
        conn.commit()
        cursor.close()
        log(f"Inserted {len(new_apps)} new games")
    else:
        log("No new games found")

    return len(new_apps)


# ============================================================================
# STEP 2: Enrich Games with SteamSpy + Steam API Data
# ============================================================================

def parse_owners(owners_str: str) -> int:
    """Parse SteamSpy owners string to integer (midpoint of range)."""
    if not owners_str or owners_str == "0":
        return 0
    try:
        parts = owners_str.replace(",", "").split("..")
        if len(parts) == 2:
            return (int(parts[0].strip()) + int(parts[1].strip())) // 2
        return int(parts[0].strip())
    except:
        return 0


def safe_int(value, default=0):
    """Safely convert value to int, handling empty strings and None."""
    if value == "" or value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def count_languages(languages_str: str) -> int:
    """Count number of supported languages from Steam's language string."""
    if not languages_str:
        return 0
    import re
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', languages_str)
    # Split by comma and count
    langs = [l.strip() for l in clean.split(',') if l.strip()]
    return len(langs)


async def fetch_steamspy_data(session: aiohttp.ClientSession, appid: int) -> Optional[Dict]:
    """Fetch data for a single app from SteamSpy."""
    try:
        url = f"{STEAMSPY_API_BASE}?request=appdetails&appid={appid}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                data = await response.json()
                if data and 'name' in data:
                    # Extract top tags as comma-separated string
                    tags_dict = data.get('tags', {})
                    top_tags = ', '.join([
                        f"{tag}" for tag, count in
                        sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)[:10]
                    ]) if tags_dict else None

                    return {
                        'appid': appid,
                        # Core dynamic metrics (use actual column names from steam_apps table)
                        'players_forever': parse_owners(data.get('owners', '0')),
                        'average_forever': safe_int(data.get('average_forever')),
                        'median_forever': safe_int(data.get('median_forever')),
                        'average_2weeks': safe_int(data.get('average_2weeks')),
                        'median_2weeks': safe_int(data.get('median_2weeks')),
                        'positive': safe_int(data.get('positive')),
                        'negative': safe_int(data.get('negative')),
                        'ccu': safe_int(data.get('ccu')),
                        'score_rank': safe_int(data.get('score_rank')),
                        # Price (dynamic - can change with sales)
                        'price': safe_int(data.get('price')),
                        'initialprice': safe_int(data.get('initialprice')),
                        # Metadata (mostly static but good to refresh)
                        'developer': data.get('developer', 'Unknown') or 'Unknown',
                        'publisher': data.get('publisher', 'Unknown') or 'Unknown',
                        'genre': data.get('genre', None),
                        'top_tags': top_tags,
                    }
    except Exception as e:
        pass
    return None


async def fetch_steam_api_data(session: aiohttp.ClientSession, appid: int) -> Optional[Dict]:
    """Fetch additional data from Steam Official API (recommendations, metacritic, platforms, etc.)."""
    try:
        url = f"{STEAM_API_BASE}?appids={appid}"
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
            if response.status == 200:
                data = await response.json()
                app_data = data.get(str(appid), {})

                if app_data.get('success'):
                    steam_data = app_data.get('data', {})
                    return {
                        'appid': appid,
                        'recommendations': steam_data.get('recommendations', {}).get('total', 0),
                        'metacritic_score': steam_data.get('metacritic', {}).get('score'),
                        'platform_windows': steam_data.get('platforms', {}).get('windows', False),
                        'platform_mac': steam_data.get('platforms', {}).get('mac', False),
                        'platform_linux': steam_data.get('platforms', {}).get('linux', False),
                        'dlc_count': len(steam_data.get('dlc', [])),
                        'achievement_count': steam_data.get('achievements', {}).get('total', 0),
                        'language_count': count_languages(steam_data.get('supported_languages', '')),
                        'required_age': safe_int(steam_data.get('required_age', 0)),
                    }
    except Exception as e:
        pass
    return None


async def fetch_full_game_data(session: aiohttp.ClientSession, appid: int, fetch_steam_api: bool = True) -> Optional[Dict]:
    """Fetch complete game data from both SteamSpy and optionally Steam Official API."""
    # Always fetch SteamSpy data first (faster, more reliable)
    steamspy_data = await fetch_steamspy_data(session, appid)

    if not steamspy_data:
        return None

    # Optionally fetch Steam API data (slower due to stricter rate limits)
    if fetch_steam_api:
        await asyncio.sleep(STEAM_API_DELAY)  # Steam API rate limit
        steam_data = await fetch_steam_api_data(session, appid)

        if steam_data:
            # Merge Steam API data into SteamSpy data
            steamspy_data.update({
                'recommendations': steam_data.get('recommendations', 0),
                'metacritic_score': steam_data.get('metacritic_score'),
                'platform_windows': steam_data.get('platform_windows', False),
                'platform_mac': steam_data.get('platform_mac', False),
                'platform_linux': steam_data.get('platform_linux', False),
                'dlc_count': steam_data.get('dlc_count', 0),
                'achievement_count': steam_data.get('achievement_count', 0),
                'language_count': steam_data.get('language_count', 0),
                'required_age': steam_data.get('required_age', 0),
            })
        else:
            # Set defaults for Steam API fields if fetch failed
            steamspy_data.update({
                'recommendations': 0,
                'metacritic_score': None,
                'platform_windows': False,
                'platform_mac': False,
                'platform_linux': False,
                'dlc_count': 0,
                'achievement_count': 0,
                'language_count': 0,
                'required_age': 0,
            })

    return steamspy_data


def update_game_in_db(cursor, data: Dict, include_steam_api: bool = True):
    """Update a single game with all dynamic fields.

    Uses the correct column names from the steam_apps table:
    - players_forever, average_forever, median_forever, average_2weeks, median_2weeks
    - positive, negative, ccu, score_rank
    - price, initialprice
    - developer, publisher, genre, top_tags
    - recommendations, metacritic_score, platform_*, dlc_count, achievement_count, language_count, required_age
    """
    if include_steam_api:
        cursor.execute("""
            UPDATE steam_apps SET
                -- SteamSpy dynamic fields
                players_forever = %s,
                average_forever = %s,
                median_forever = %s,
                average_2weeks = %s,
                median_2weeks = %s,
                positive = %s,
                negative = %s,
                ccu = %s,
                score_rank = %s,
                price = %s,
                initialprice = %s,
                developer = %s,
                publisher = %s,
                genre = %s,
                top_tags = %s,
                -- Steam API dynamic fields
                recommendations = %s,
                metacritic_score = %s,
                platform_windows = %s,
                platform_mac = %s,
                platform_linux = %s,
                dlc_count = %s,
                achievement_count = %s,
                language_count = %s,
                required_age = %s,
                updated_at = %s
            WHERE appid = %s
        """, (
            data['players_forever'],
            data['average_forever'],
            data['median_forever'],
            data.get('average_2weeks', 0),
            data.get('median_2weeks', 0),
            data['positive'],
            data['negative'],
            data['ccu'],
            data.get('score_rank', 0),
            data['price'],
            data['initialprice'],
            data.get('developer', 'Unknown'),
            data.get('publisher', 'Unknown'),
            data.get('genre'),
            data.get('top_tags'),
            data.get('recommendations', 0),
            data.get('metacritic_score'),
            data.get('platform_windows', False),
            data.get('platform_mac', False),
            data.get('platform_linux', False),
            data.get('dlc_count', 0),
            data.get('achievement_count', 0),
            data.get('language_count', 0),
            data.get('required_age', 0),
            datetime.now(),
            data['appid']
        ))
    else:
        # SteamSpy-only update (faster, for bulk refresh)
        cursor.execute("""
            UPDATE steam_apps SET
                players_forever = %s,
                average_forever = %s,
                median_forever = %s,
                average_2weeks = %s,
                median_2weeks = %s,
                positive = %s,
                negative = %s,
                ccu = %s,
                score_rank = %s,
                price = %s,
                initialprice = %s,
                developer = %s,
                publisher = %s,
                genre = %s,
                top_tags = %s,
                updated_at = %s
            WHERE appid = %s
        """, (
            data['players_forever'],
            data['average_forever'],
            data['median_forever'],
            data.get('average_2weeks', 0),
            data.get('median_2weeks', 0),
            data['positive'],
            data['negative'],
            data['ccu'],
            data.get('score_rank', 0),
            data['price'],
            data['initialprice'],
            data.get('developer', 'Unknown'),
            data.get('publisher', 'Unknown'),
            data.get('genre'),
            data.get('top_tags'),
            datetime.now(),
            data['appid']
        ))


async def enrich_games(conn) -> int:
    """Enrich games that don't have owner data yet.

    Fetches from BOTH SteamSpy AND Steam Official API for complete data.
    """
    log("=" * 60)
    log("STEP 2: Enriching games with SteamSpy + Steam API data")
    log("=" * 60)

    # Find games needing enrichment (no owner data)
    # Use correct column name: players_forever (not total_owners)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT appid FROM steam_apps
        WHERE players_forever IS NULL OR players_forever = 0
        ORDER BY created_at DESC
        LIMIT %s
    """, (MAX_ENRICHMENTS_PER_RUN,))
    appids = [row[0] for row in cursor.fetchall()]
    cursor.close()

    if not appids:
        log("No games need enrichment")
        return 0

    log(f"Enriching {len(appids)} games with full data (SteamSpy + Steam API)...")

    enriched_data = []
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async def fetch_with_semaphore(session, appid):
        async with semaphore:
            # Fetch full data including Steam API for new games
            result = await fetch_full_game_data(session, appid, fetch_steam_api=True)
            await asyncio.sleep(STEAMSPY_APP_DELAY)
            return result

    ssl_context = False  # Disable SSL verification for compatibility
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_with_semaphore(session, appid) for appid in appids]

        # Process with progress updates
        for i, task in enumerate(asyncio.as_completed(tasks)):
            result = await task
            if result:
                enriched_data.append(result)

            if (i + 1) % 100 == 0:
                log(f"  Progress: {i + 1}/{len(appids)} ({len(enriched_data)} enriched)")

    # Update database with ALL dynamic fields
    if enriched_data:
        log(f"Updating {len(enriched_data)} games in database with all dynamic fields...")
        cursor = conn.cursor()

        for data in enriched_data:
            update_game_in_db(cursor, data, include_steam_api=True)

        conn.commit()
        cursor.close()
        log(f"Updated {len(enriched_data)} games with full data")

    return len(enriched_data)


# ============================================================================
# STEP 2b: Refresh Existing Games (price changes, new reviews, etc.)
# ============================================================================

async def refresh_existing_games(conn) -> int:
    """Refresh existing games that haven't been updated recently.

    This catches ALL dynamic data points:
    - Price changes and discounts
    - New reviews and rating changes
    - Updated owner counts
    - Playtime changes (forever and 2-week)
    - CCU (concurrent users)
    - Score rank changes
    - Tag changes
    - DLC/achievement updates (for top games)
    """
    log("=" * 60)
    log("STEP 2b: Refreshing existing games with ALL dynamic data")
    log("=" * 60)

    # Find games that need refreshing (not updated in X days)
    # Prioritize popular games (more owners = more important to keep fresh)
    # Use correct column name: players_forever (not total_owners)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT appid, players_forever FROM steam_apps
        WHERE players_forever IS NOT NULL
          AND players_forever > 0
          AND updated_at < NOW() - INTERVAL '%s days'
        ORDER BY players_forever DESC
        LIMIT %s
    """, (REFRESH_OLDER_THAN_DAYS, MAX_UPDATES_PER_RUN))
    games = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.close()

    if not games:
        log("No games need refreshing")
        return 0

    # Separate into high-priority (Steam API too) and normal (SteamSpy only)
    # Top 100 games get full refresh including Steam API
    HIGH_PRIORITY_COUNT = 100
    high_priority_appids = [g[0] for g in games[:HIGH_PRIORITY_COUNT]]
    normal_appids = [g[0] for g in games[HIGH_PRIORITY_COUNT:]]

    log(f"Refreshing {len(games)} existing games:")
    log(f"  - {len(high_priority_appids)} high-priority (full Steam API refresh)")
    log(f"  - {len(normal_appids)} normal (SteamSpy only - faster)")

    refreshed_data = []
    semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

    async def fetch_high_priority(session, appid):
        async with semaphore:
            # Full refresh including Steam API for popular games
            result = await fetch_full_game_data(session, appid, fetch_steam_api=True)
            await asyncio.sleep(STEAMSPY_APP_DELAY)
            return (result, True) if result else None

    async def fetch_normal(session, appid):
        async with semaphore:
            # SteamSpy only for faster bulk refresh
            result = await fetch_steamspy_data(session, appid)
            await asyncio.sleep(STEAMSPY_APP_DELAY)
            return (result, False) if result else None

    ssl_context = False
    connector = aiohttp.TCPConnector(ssl=ssl_context)

    async with aiohttp.ClientSession(connector=connector) as session:
        # Process high-priority games first
        if high_priority_appids:
            log(f"  Fetching high-priority games with Steam API...")
            tasks = [fetch_high_priority(session, appid) for appid in high_priority_appids]

            for i, task in enumerate(asyncio.as_completed(tasks)):
                result = await task
                if result:
                    refreshed_data.append(result)

                if (i + 1) % 50 == 0:
                    log(f"    High-priority progress: {i + 1}/{len(high_priority_appids)}")

        # Process normal games (SteamSpy only)
        if normal_appids:
            log(f"  Fetching normal games (SteamSpy only)...")
            tasks = [fetch_normal(session, appid) for appid in normal_appids]

            for i, task in enumerate(asyncio.as_completed(tasks)):
                result = await task
                if result:
                    refreshed_data.append(result)

                if (i + 1) % 200 == 0:
                    log(f"    Normal progress: {i + 1}/{len(normal_appids)}")

    # Update database with fresh data
    if refreshed_data:
        log(f"Updating {len(refreshed_data)} games with fresh dynamic data...")
        cursor = conn.cursor()

        for data, include_steam_api in refreshed_data:
            update_game_in_db(cursor, data, include_steam_api=include_steam_api)

        conn.commit()
        cursor.close()
        log(f"Refreshed {len(refreshed_data)} existing games with all dynamic fields")

    return len(refreshed_data)


# ============================================================================
# STEP 3: Update Analytics Tables
# ============================================================================

def update_analytics(conn):
    """Update derived analytics tables.

    Transforms raw steam_apps columns to friendly fact_game_metrics columns:
    - players_forever -> total_owners
    - average_forever -> avg_hours_played (with /60 conversion from minutes to hours)
    - median_forever -> median_hours_played (with /60 conversion)
    - positive -> positive_reviews
    - negative -> negative_reviews
    - price -> price_usd (with /100 conversion from cents to dollars)
    - initialprice -> initialprice_usd
    - top_tags -> top_tags
    """
    log("=" * 60)
    log("STEP 3: Updating analytics tables")
    log("=" * 60)

    cursor = conn.cursor()

    # Update fact_game_metrics
    # Read from steam_apps using correct raw column names, transform to friendly names
    # Use TRUNCATE + INSERT for full refresh (faster and cleaner than upsert)
    log("Refreshing fact_game_metrics...")
    cursor.execute("TRUNCATE TABLE fact_game_metrics")
    cursor.execute("""
        INSERT INTO fact_game_metrics (
            appid, name, developer, publisher,
            price_usd, initialprice_usd, price_category,
            total_owners, positive_reviews, negative_reviews, total_reviews,
            rating_percentage, review_category,
            avg_hours_played, median_hours_played, ccu,
            hours_per_dollar, engagement_score,
            genres, top_tags,
            created_at, updated_at
        )
        SELECT
            appid,
            name,
            developer,
            publisher,
            CASE WHEN price > 0 THEN price / 100.0 ELSE 0 END as price_usd,
            CASE WHEN initialprice > 0 THEN initialprice / 100.0 ELSE 0 END as initialprice_usd,
            CASE
                WHEN price = 0 THEN 'Free'
                WHEN price <= 500 THEN 'Budget ($0-$5)'
                WHEN price <= 1000 THEN 'Low ($5-$10)'
                WHEN price <= 2000 THEN 'Medium ($10-$20)'
                WHEN price <= 3000 THEN 'Standard ($20-$30)'
                WHEN price <= 5000 THEN 'Premium ($30-$50)'
                ELSE 'AAA ($50+)'
            END as price_category,
            players_forever as total_owners,
            positive as positive_reviews,
            negative as negative_reviews,
            COALESCE(positive, 0) + COALESCE(negative, 0) as total_reviews,
            CASE
                WHEN COALESCE(positive, 0) + COALESCE(negative, 0) > 0
                THEN ROUND((100.0 * positive / (positive + negative))::numeric, 1)
                ELSE NULL
            END as rating_percentage,
            CASE
                WHEN COALESCE(positive, 0) + COALESCE(negative, 0) < 10 THEN 'Insufficient Reviews'
                WHEN 100.0 * positive / NULLIF(positive + negative, 0) >= 95 THEN 'Overwhelmingly Positive'
                WHEN 100.0 * positive / NULLIF(positive + negative, 0) >= 80 THEN 'Very Positive'
                WHEN 100.0 * positive / NULLIF(positive + negative, 0) >= 70 THEN 'Mostly Positive'
                WHEN 100.0 * positive / NULLIF(positive + negative, 0) >= 40 THEN 'Mixed'
                WHEN 100.0 * positive / NULLIF(positive + negative, 0) >= 20 THEN 'Mostly Negative'
                ELSE 'Overwhelmingly Negative'
            END as review_category,
            CASE WHEN average_forever > 0 THEN average_forever / 60.0 ELSE NULL END as avg_hours_played,
            CASE WHEN median_forever > 0 THEN median_forever / 60.0 ELSE NULL END as median_hours_played,
            ccu,
            CASE
                WHEN price > 0 AND average_forever > 0
                THEN ROUND(((average_forever / 60.0) / (price / 100.0))::numeric, 2)
                ELSE NULL
            END as hours_per_dollar,
            CASE
                WHEN players_forever > 0 AND average_forever > 0
                THEN ROUND((LOG(players_forever + 1) * (average_forever / 60.0))::numeric, 2)
                ELSE NULL
            END as engagement_score,
            genre as genres,
            top_tags,
            created_at,
            NOW() as updated_at
        FROM steam_apps
        WHERE players_forever IS NOT NULL AND players_forever > 0
    """)
    conn.commit()

    # Update aggregate tables
    log("Refreshing aggregate tables...")

    # Price tier stats - TRUNCATE and re-insert
    cursor.execute("TRUNCATE TABLE agg_price_tier_stats")
    cursor.execute("""
        INSERT INTO agg_price_tier_stats (
            price_category, sort_order, game_count,
            avg_owners, median_owners, avg_rating, avg_playtime_hours,
            avg_hours_per_dollar, games_90plus_rating, games_1m_plus_owners, success_rate_100k
        )
        SELECT
            price_category,
            CASE price_category
                WHEN 'Free' THEN 1
                WHEN 'Budget ($0-$5)' THEN 2
                WHEN 'Low ($5-$10)' THEN 3
                WHEN 'Medium ($10-$20)' THEN 4
                WHEN 'Standard ($20-$30)' THEN 5
                WHEN 'Premium ($30-$50)' THEN 6
                WHEN 'AAA ($50+)' THEN 7
            END as sort_order,
            COUNT(*) as game_count,
            ROUND(AVG(total_owners)::numeric) as avg_owners,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_owners) as median_owners,
            ROUND(AVG(rating_percentage)::numeric, 1) as avg_rating,
            ROUND(AVG(avg_hours_played)::numeric, 1) as avg_playtime_hours,
            ROUND(AVG(hours_per_dollar)::numeric, 2) as avg_hours_per_dollar,
            COUNT(*) FILTER (WHERE rating_percentage >= 90) as games_90plus_rating,
            COUNT(*) FILTER (WHERE total_owners >= 1000000) as games_1m_plus_owners,
            ROUND((100.0 * COUNT(*) FILTER (WHERE total_owners >= 100000) / NULLIF(COUNT(*), 0))::numeric, 1) as success_rate_100k
        FROM fact_game_metrics
        WHERE price_category IS NOT NULL
        GROUP BY price_category
    """)
    conn.commit()

    # Log refresh - TRUNCATE and re-insert
    cursor.execute("DELETE FROM agg_refresh_log WHERE table_name = 'daily_refresh'")
    cursor.execute("""
        INSERT INTO agg_refresh_log (table_name, last_refreshed, row_count)
        VALUES ('daily_refresh', NOW(), 0)
    """)
    conn.commit()

    cursor.close()
    log("Analytics tables updated")


# ============================================================================
# STEP 4: Remove Stale Apps (no longer in SteamSpy)
# ============================================================================

def remove_stale_apps(conn) -> int:
    """Remove apps that no longer exist in SteamSpy.

    This checks a sample of our oldest-updated apps against SteamSpy.
    If an app returns no data from SteamSpy, it's likely been removed.

    We remove from both steam_apps and fact_game_metrics.
    """
    import requests

    log("=" * 60)
    log("STEP 4: Checking for removed apps")
    log("=" * 60)

    # Get apps that haven't been updated in a long time (potential candidates for removal)
    # Check oldest 100 apps that we haven't verified recently
    cursor = conn.cursor()
    cursor.execute("""
        SELECT appid, name FROM steam_apps
        WHERE updated_at < NOW() - INTERVAL '30 days'
        ORDER BY updated_at ASC
        LIMIT 100
    """)
    candidates = [(row[0], row[1]) for row in cursor.fetchall()]
    cursor.close()

    if not candidates:
        log("No stale apps to check")
        return 0

    log(f"Checking {len(candidates)} apps for removal...")

    removed_appids = []

    for appid, name in candidates:
        try:
            # Check if app still exists in SteamSpy
            url = f"{STEAMSPY_API_BASE}?request=appdetails&appid={appid}"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # SteamSpy returns empty or minimal data for removed apps
                if not data or data.get('name') == '' or data.get('name') is None:
                    log(f"  App {appid} ({name}) no longer exists - marking for removal")
                    removed_appids.append(appid)
            else:
                # Don't remove on API errors, just skip
                pass

            # Rate limit
            time.sleep(0.5)

        except Exception as e:
            # Don't remove on errors, just skip
            pass

        # Stop after checking a reasonable number to avoid long runtimes
        if len(removed_appids) >= 20:
            log("  Reached removal limit for this run")
            break

    # Remove the apps
    if removed_appids:
        log(f"Removing {len(removed_appids)} apps from database...")
        cursor = conn.cursor()

        # Remove from fact_game_metrics first (foreign key constraint)
        cursor.execute("""
            DELETE FROM fact_game_metrics WHERE appid = ANY(%s)
        """, (removed_appids,))

        # Remove from steam_apps
        cursor.execute("""
            DELETE FROM steam_apps WHERE appid = ANY(%s)
        """, (removed_appids,))

        conn.commit()
        cursor.close()
        log(f"Removed {len(removed_appids)} stale apps")
    else:
        log("No apps need removal")

    return len(removed_appids)


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='PlayIntel Daily Data Refresh')
    parser.add_argument('--fetch-only', action='store_true', help='Only fetch new games')
    parser.add_argument('--enrich-only', action='store_true', help='Only enrich new games (no owner data)')
    parser.add_argument('--refresh-only', action='store_true', help='Only refresh existing games (stale data)')
    parser.add_argument('--analytics-only', action='store_true', help='Only update analytics')
    parser.add_argument('--cleanup-only', action='store_true', help='Only remove stale apps')
    args = parser.parse_args()

    start_time = time.time()

    log("=" * 60)
    log("PlayIntel Daily Data Refresh")
    log("=" * 60)

    try:
        conn = get_db_connection()
        log("Connected to database")

        new_games = 0
        enriched = 0
        refreshed = 0
        removed = 0

        # Determine what to run
        run_all = not (args.fetch_only or args.enrich_only or args.refresh_only or args.analytics_only or args.cleanup_only)

        if run_all or args.fetch_only:
            new_games = fetch_new_games(conn)

        if run_all or args.enrich_only:
            enriched = asyncio.run(enrich_games(conn))

        if run_all or args.refresh_only:
            refreshed = asyncio.run(refresh_existing_games(conn))

        if run_all or args.cleanup_only:
            removed = remove_stale_apps(conn)

        if run_all or args.analytics_only:
            update_analytics(conn)

        conn.close()

        elapsed = time.time() - start_time
        log("=" * 60)
        log("COMPLETE!")
        log(f"  New games fetched: {new_games}")
        log(f"  New games enriched: {enriched}")
        log(f"  Existing games refreshed: {refreshed}")
        log(f"  Stale games removed: {removed}")
        log(f"  Total time: {elapsed/60:.1f} minutes")
        log("=" * 60)

        return 0

    except Exception as e:
        log(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
