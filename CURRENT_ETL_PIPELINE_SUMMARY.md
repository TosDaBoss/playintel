# Current ETL Pipeline Summary

## Your Existing 3-Script Pipeline

You have **3 scripts** that work together to build your Steam analytics database:

---

## Script 1: `steam_to_postgres.py` - Initial Data Load

### What it does:
Fetches **basic app list** from SteamSpy and creates the foundation table.

### Columns it creates in `steam_apps` table:
1. `appid` (PRIMARY KEY) - Unique Steam app ID
2. `name` - Game name
3. `created_at` - Record creation timestamp
4. `updated_at` - Record update timestamp

### Data Source:
- **SteamSpy API:** `https://steamspy.com/api.php?request=all&page={page}`
- Fetches paginated data (1000 apps per page)
- Rate limit: 1 request per 60 seconds
- Target: 4,000 apps (configurable with `MAX_APPS_TO_FETCH`)

### What it brings in:
```json
{
  "appid": 730,
  "name": "Counter-Strike 2"
}
```

**Only 2 fields** - just the basics!

---

## Script 2: `enrich_steam_data_fast.py` - Enrich with Details

### What it does:
Adds **detailed metrics** from SteamSpy to existing apps using **async/concurrent requests** (4x faster than sequential).

### Columns it adds to `steam_apps` table:
5. `players_forever` - Total player count (owner estimate)
6. `average_forever` - Average playtime (in **minutes**)
7. `price` - Current price (in **cents**)
8. `initialprice` - Original price (in **cents**)
9. `positive` - Positive review count
10. `negative` - Negative review count
11. `score_rank` - SteamSpy ranking
12. `developer` - Developer name
13. `publisher` - Publisher name

### Data Source:
- **SteamSpy API:** `https://steamspy.com/api.php?request=appdetails&appid={appid}`
- Concurrent requests: 4 per second
- Rate limit: 4 req/sec (0.25s delay between requests)
- Batch size: 100 apps at a time

### What it brings in:
```json
{
  "appid": 730,
  "players_forever": 50000000,
  "average_forever": 32997,      // minutes
  "price": 0,                    // cents
  "initialprice": 0,             // cents
  "positive": 7642084,
  "negative": 1173003,
  "score_rank": "",
  "developer": "Valve",
  "publisher": "Valve"
}
```

**9 additional fields** - core metrics!

---

## Script 3: `create_analytics_tables.py` - Transform into Analytics Tables

### What it does:
Transforms raw `steam_apps` data into **analytics-ready tables** with calculated metrics and dimensions for Power BI.

### Phase 1: Adds derived columns to `steam_apps` table:
14. `price_usd` - Price in dollars (converted from cents)
15. `initialprice_usd` - Original price in dollars
16. `avg_hours_played` - Playtime in hours (converted from minutes)
17. `total_reviews` - Calculated: positive + negative
18. `rating_percentage` - Calculated: (positive / total) * 100
19. `review_category` - Text: "Very Positive", "Mixed", etc.
20. `is_free` - Boolean: price == 0
21. `has_discount` - Boolean: price < initialprice
22. `discount_percentage` - Calculated: ((initialprice - price) / initialprice) * 100
23. `price_category` - Text: "Budget ($0-$5)", "Medium ($10-$20)", etc.
24. `hours_per_dollar` - Calculated: avg_hours / price_usd
25. `engagement_score` - Calculated: avg_hours * rating * log(players)

### Phase 2: Creates analytics tables:

#### **fact_game_metrics** (main analysis table)
- Mirrors `steam_apps` with filtered data (players_forever > 0 OR total_reviews > 10)
- 27 columns total
- Primary key: appid
- Indexes on: developer, publisher, price_category

#### **dim_developers** (developer performance)
- Aggregated developer stats:
  - Total games, paid/free breakdown
  - Total/average owners
  - Average/max playtime
  - Review metrics
  - Pricing metrics
  - Value metrics (hours per dollar, engagement score)

#### **dim_publishers** (publisher performance)
- Same structure as dim_developers but for publishers

#### **analysis_price_playtime** (playtime by price range)
- Aggregated stats per price_category
- Shows: game count, avg price, avg playtime, avg value, etc.

#### **analysis_reviews_playtime** (playtime by review rating)
- Aggregated stats per review_category
- Shows correlation between ratings and playtime

#### **top_value_games** (best value games)
- Top 1000 games by hours_per_dollar
- Filtered: price > 0, reviews >= 50, rating >= 70%

#### **summary_stats** (overall KPIs)
- Single-row summary with totals and averages

---

## Complete Column List from Your Pipeline

### In `steam_apps` table (25 columns):
1. `appid` - *(from script 1)*
2. `name` - *(from script 1)*
3. `created_at` - *(from script 1)*
4. `updated_at` - *(from script 1)*
5. `players_forever` - *(from script 2)* **→ This is "total_owners"**
6. `average_forever` - *(from script 2)* in minutes
7. `price` - *(from script 2)* in cents
8. `initialprice` - *(from script 2)* in cents
9. `positive` - *(from script 2)*
10. `negative` - *(from script 2)*
11. `score_rank` - *(from script 2)*
12. `developer` - *(from script 2)*
13. `publisher` - *(from script 2)*
14. `price_usd` - *(from script 3)* calculated
15. `initialprice_usd` - *(from script 3)* calculated
16. `avg_hours_played` - *(from script 3)* calculated from average_forever
17. `total_reviews` - *(from script 3)* calculated
18. `rating_percentage` - *(from script 3)* calculated
19. `review_category` - *(from script 3)* calculated
20. `is_free` - *(from script 3)* calculated
21. `has_discount` - *(from script 3)* calculated
22. `discount_percentage` - *(from script 3)* calculated
23. `price_category` - *(from script 3)* calculated
24. `hours_per_dollar` - *(from script 3)* calculated
25. `engagement_score` - *(from script 3)* calculated

### In `fact_game_metrics` table (27 columns):
All 25 columns above **EXCEPT**:
- ❌ `players_forever` (renamed to `total_owners`)
- ❌ `average_forever` (not included, replaced by `avg_hours_played`)
- ❌ `price` (not included, replaced by `price_usd`)
- ❌ `initialprice` (not included, replaced by `initialprice_usd`)
- ❌ `positive` (renamed to `positive_reviews`)
- ❌ `negative` (renamed to `negative_reviews`)

**PLUS these 2 new columns:**
- ✅ `total_owners` (renamed from `players_forever`)
- ✅ `positive_reviews` (renamed from `positive`)
- ✅ `negative_reviews` (renamed from `negative`)

Total: 19 columns in fact_game_metrics

**WAIT - You said 27 columns in fact_game_metrics!**

Let me check your actual schema again...

---

## **THE PROBLEM: Missing Owner Data**

Your `fact_game_metrics` table has a column called `total_owners`, but:

**Issue:** `enrich_steam_data_fast.py` populates `players_forever` in the `steam_apps` table.

**Issue:** `create_analytics_tables.py` maps `players_forever as total_owners` when creating `fact_game_metrics`.

**Issue:** BUT your current `fact_game_metrics` table shows `total_owners = NULL` for all 4,928 games.

**Root Cause Options:**
1. **Script 2 was never run** - `players_forever` is NULL in `steam_apps`
2. **Script 2 failed** - `players_forever` is 0 in `steam_apps`
3. **Script 3 filter too strict** - WHERE clause excluded all games
4. **Someone manually created `fact_game_metrics`** - bypassing script 3

---

## Diagnosis: Let's Check

Run this to see what happened:

```bash
python3 -c "
import psycopg
conn = psycopg.connect('postgresql://postgres:YOUR_PASSWORD@localhost:5432/steam_apps_db')
cursor = conn.cursor()

# Check steam_apps table
cursor.execute('SELECT COUNT(*) FROM steam_apps WHERE players_forever IS NULL')
null_players = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM steam_apps WHERE players_forever = 0')
zero_players = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM steam_apps WHERE players_forever > 0')
has_players = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM steam_apps')
total = cursor.fetchone()[0]

print('steam_apps table:')
print(f'  Total records: {total}')
print(f'  players_forever IS NULL: {null_players}')
print(f'  players_forever = 0: {zero_players}')
print(f'  players_forever > 0: {has_players}')

# Check if players_forever column exists
cursor.execute(\"\"\"
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'steam_apps'
    AND column_name = 'players_forever'
\"\"\")
col_exists = cursor.fetchone()
print(f'\n  players_forever column exists: {col_exists is not None}')

conn.close()
"
```

---

## Summary: Your 3-Script Pipeline

| Script | Purpose | Columns Added | Data Source |
|--------|---------|---------------|-------------|
| 1. `steam_to_postgres.py` | Initial load | 4 (appid, name, timestamps) | SteamSpy paginated API |
| 2. `enrich_steam_data_fast.py` | Add metrics | 9 (players, playtime, reviews, price, dev/pub) | SteamSpy app details API |
| 3. `create_analytics_tables.py` | Transform for BI | 12 calculated + 7 analysis tables | Calculates from steam_apps |

**Total columns in steam_apps:** 25
**Total columns in fact_game_metrics:** 19 (filtered & renamed)

**Problem:** Script 2 likely wasn't run, so `players_forever` (which becomes `total_owners`) is NULL.

**Solution:** Run `enrich_steam_data_fast.py` to populate the missing data.
