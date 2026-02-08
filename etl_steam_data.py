#!/usr/bin/env python3
"""
ETL Pipeline for Steam Market Data
Fetches data from Steam API and SteamSpy, then updates PostgreSQL database.

Usage:
    python3 etl_steam_data.py [--limit 100] [--update-existing]

Options:
    --limit N           Only process N games (for testing)
    --update-existing   Update existing games in database
"""

import os
import sys
import time
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from datetime import datetime
import argparse

# Load environment variables
load_dotenv('/Users/tosdaboss/playintel/backend/.env')

DATABASE_URL = os.getenv("DATABASE_URL")

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(DATABASE_URL)


def fetch_all_steam_apps():
    """Fetch complete list of Steam apps from Steam API."""
    print(f"{BLUE}Fetching complete Steam app list...{RESET}")

    try:
        # Use the new recommended endpoint
        response = requests.get(
            "https://api.steampowered.com/IStoreService/GetAppList/v1/",
            params={"key": "", "include_games": True, "max_results": 50000},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            apps = data.get("response", {}).get("apps", [])
            print(f"{GREEN}✓ Found {len(apps)} Steam apps{RESET}")
            return apps
        else:
            # Fallback to old endpoint if new one fails
            print(f"{YELLOW}New endpoint failed, trying legacy endpoint...{RESET}")
            response = requests.get(
                "https://api.steampowered.com/ISteamApps/GetAppList/v2/",
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                apps = data.get("applist", {}).get("apps", [])
                print(f"{GREEN}✓ Found {len(apps)} Steam apps{RESET}")
                return apps
            else:
                print(f"{RED}✗ Failed to fetch Steam app list{RESET}")
                return []

    except Exception as e:
        print(f"{RED}Error fetching Steam apps: {e}{RESET}")
        return []


def fetch_steam_app_details(appid):
    """Fetch detailed information for a specific app from Steam API."""
    try:
        response = requests.get(
            f"https://store.steampowered.com/api/appdetails",
            params={"appids": appid},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            app_data = data.get(str(appid), {})

            if app_data.get("success"):
                return app_data.get("data", {})

        return None

    except Exception as e:
        print(f"{RED}Error fetching Steam details for {appid}: {e}{RESET}")
        return None


def fetch_steamspy_data(appid):
    """Fetch owner and playtime data from SteamSpy API."""
    try:
        response = requests.get(
            "https://steamspy.com/api.php",
            params={"request": "appdetails", "appid": appid},
            timeout=10
        )

        if response.status_code == 200:
            return response.json()

        return None

    except Exception as e:
        print(f"{RED}Error fetching SteamSpy data for {appid}: {e}{RESET}")
        return None


def parse_owners_range(owners_str):
    """
    Parse SteamSpy owners string (e.g., "20,000 .. 50,000") into integer.
    Returns the midpoint of the range.
    """
    if not owners_str or owners_str == "0":
        return 0

    try:
        # Remove commas and split by ".."
        parts = owners_str.replace(",", "").split("..")

        if len(parts) == 2:
            low = int(parts[0].strip())
            high = int(parts[1].strip())
            return (low + high) // 2
        else:
            # Single number
            return int(parts[0].strip())

    except Exception as e:
        print(f"{YELLOW}Warning: Could not parse owners '{owners_str}': {e}{RESET}")
        return 0


def process_game(app, update_existing=False):
    """
    Process a single game: fetch data from Steam and SteamSpy, then insert/update in DB.

    Returns: (success: bool, game_data: dict or None)
    """
    appid = app.get("appid")
    name = app.get("name", "Unknown")

    if not appid:
        return False, None

    # Fetch Steam details
    steam_data = fetch_steam_app_details(appid)

    if not steam_data:
        return False, None

    # Filter out non-games (DLC, software, etc.)
    app_type = steam_data.get("type", "")
    if app_type not in ["game"]:
        return False, None

    # Rate limiting: 1 request per 4 seconds for SteamSpy
    time.sleep(4)

    # Fetch SteamSpy data for owner counts and playtime
    steamspy_data = fetch_steamspy_data(appid)

    # Parse data
    game_data = {
        "appid": appid,
        "name": steam_data.get("name", name),
        "developer": ", ".join(steam_data.get("developers", [])) if steam_data.get("developers") else None,
        "publisher": ", ".join(steam_data.get("publishers", [])) if steam_data.get("publishers") else None,
        "release_date": steam_data.get("release_date", {}).get("date"),
        "is_free": steam_data.get("is_free", False),
        "price_usd": steam_data.get("price_overview", {}).get("final", 0) / 100.0 if steam_data.get("price_overview") else 0.0,
        "genres": ", ".join([g.get("description", "") for g in steam_data.get("genres", [])]),
        "categories": ", ".join([c.get("description", "") for c in steam_data.get("categories", [])]),
    }

    # Add SteamSpy data
    if steamspy_data:
        owners_str = steamspy_data.get("owners", "0")
        game_data["total_owners"] = parse_owners_range(owners_str)
        game_data["avg_hours_played"] = steamspy_data.get("average_forever", 0) / 60.0  # Convert minutes to hours
        game_data["median_hours_played"] = steamspy_data.get("median_forever", 0) / 60.0
        game_data["ccu"] = steamspy_data.get("ccu", 0)  # Peak concurrent users
    else:
        game_data["total_owners"] = 0
        game_data["avg_hours_played"] = 0
        game_data["median_hours_played"] = 0
        game_data["ccu"] = 0

    # Calculate derived metrics
    if game_data["price_usd"] > 0 and game_data["avg_hours_played"] > 0:
        game_data["hours_per_dollar"] = game_data["avg_hours_played"] / game_data["price_usd"]
    else:
        game_data["hours_per_dollar"] = 0

    return True, game_data


def insert_or_update_game(conn, game_data, update_existing=False):
    """Insert or update game data in the database."""
    cursor = conn.cursor()

    try:
        if update_existing:
            # Update existing record
            cursor.execute("""
                UPDATE fact_game_metrics
                SET
                    name = %s,
                    developer = %s,
                    publisher = %s,
                    release_date = %s,
                    is_free = %s,
                    price_usd = %s,
                    genres = %s,
                    categories = %s,
                    total_owners = %s,
                    avg_hours_played = %s,
                    median_hours_played = %s,
                    ccu = %s,
                    hours_per_dollar = %s,
                    updated_at = NOW()
                WHERE appid = %s
            """, (
                game_data["name"],
                game_data["developer"],
                game_data["publisher"],
                game_data["release_date"],
                game_data["is_free"],
                game_data["price_usd"],
                game_data["genres"],
                game_data["categories"],
                game_data["total_owners"],
                game_data["avg_hours_played"],
                game_data["median_hours_played"],
                game_data["ccu"],
                game_data["hours_per_dollar"],
                game_data["appid"]
            ))
        else:
            # Insert new record (ignore if exists)
            cursor.execute("""
                INSERT INTO fact_game_metrics (
                    appid, name, developer, publisher, release_date, is_free,
                    price_usd, genres, categories, total_owners, avg_hours_played,
                    median_hours_played, ccu, hours_per_dollar, created_at, updated_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                ON CONFLICT (appid) DO NOTHING
            """, (
                game_data["appid"],
                game_data["name"],
                game_data["developer"],
                game_data["publisher"],
                game_data["release_date"],
                game_data["is_free"],
                game_data["price_usd"],
                game_data["genres"],
                game_data["categories"],
                game_data["total_owners"],
                game_data["avg_hours_played"],
                game_data["median_hours_played"],
                game_data["ccu"],
                game_data["hours_per_dollar"]
            ))

        conn.commit()
        return True

    except Exception as e:
        print(f"{RED}Error inserting/updating game {game_data['appid']}: {e}{RESET}")
        conn.rollback()
        return False


def main():
    """Main ETL pipeline."""
    parser = argparse.ArgumentParser(description="ETL Pipeline for Steam Market Data")
    parser.add_argument("--limit", type=int, help="Limit number of games to process (for testing)")
    parser.add_argument("--update-existing", action="store_true", help="Update existing games in database")
    args = parser.parse_args()

    print(f"\n{BLUE}{'='*80}")
    print(f"Steam Market Data ETL Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}{RESET}\n")

    # Fetch all Steam apps
    apps = fetch_all_steam_apps()

    if not apps:
        print(f"{RED}No apps found. Exiting.{RESET}")
        return

    # Apply limit if specified
    if args.limit:
        apps = apps[:args.limit]
        print(f"{YELLOW}Processing limited to {args.limit} apps{RESET}\n")

    # Connect to database
    conn = get_db_connection()

    # Process each app
    total = len(apps)
    successful = 0
    failed = 0
    skipped = 0

    for i, app in enumerate(apps, 1):
        appid = app.get("appid")
        name = app.get("name", "Unknown")

        print(f"[{i}/{total}] Processing: {name} (ID: {appid})")

        success, game_data = process_game(app, update_existing=args.update_existing)

        if success and game_data:
            if insert_or_update_game(conn, game_data, update_existing=args.update_existing):
                successful += 1
                print(f"{GREEN}✓ Inserted/Updated: {game_data['name']} (Owners: {game_data['total_owners']:,}){RESET}\n")
            else:
                failed += 1
        else:
            skipped += 1
            print(f"{YELLOW}⊘ Skipped (not a game or no data){RESET}\n")

    conn.close()

    # Final report
    print(f"\n{BLUE}{'='*80}")
    print(f"ETL Pipeline Complete")
    print(f"{'='*80}{RESET}")
    print(f"Total Processed: {total}")
    print(f"{GREEN}Successful: {successful}{RESET}")
    print(f"{YELLOW}Skipped: {skipped}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}ETL interrupted by user{RESET}")
    except Exception as e:
        print(f"\n{RED}ETL error: {e}{RESET}")
        import traceback
        traceback.print_exc()
