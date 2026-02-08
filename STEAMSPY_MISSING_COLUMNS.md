# SteamSpy Available vs Current Database - Missing Columns

## SteamSpy API Response (18 fields total)

### ✅ Already Have (9 fields)
These are fetched by your `enrich_steam_data_fast.py`:

1. ✅ `appid` → you have: `appid`
2. ✅ `name` → you have: `name`
3. ✅ `developer` → you have: `developer`
4. ✅ `publisher` → you have: `publisher`
5. ✅ `positive` → you have: `positive_reviews`
6. ✅ `negative` → you have: `negative_reviews`
7. ✅ `owners` → you have: `total_owners` (currently NULL/0 - needs `enrich_steam_data_fast.py` to run)
8. ✅ `average_forever` → you have: `avg_hours_played` (converted from minutes to hours)
9. ✅ `price` → you have: `price_usd` (converted from cents to dollars)
10. ✅ `initialprice` → you have: `initialprice_usd` (converted from cents to dollars)
11. ✅ `score_rank` → you have: `score_rank`
12. ✅ `discount` → you have: `discount_percentage` (calculated by script 3)

---

## ❌ Missing from Your Database (6 fields)

These are available from SteamSpy but NOT in your current pipeline:

### 1. `median_forever` (Median playtime - all time)
- **Type:** Integer (minutes)
- **Description:** Median playtime across all players who own the game (all time)
- **Why it matters:** Better metric than average - not skewed by outliers (e.g., players who idle for 10,000 hours)
- **Database column:** `median_hours_played` (column exists but is NULL)
- **Conversion needed:** Divide by 60 to convert minutes → hours

### 2. `average_2weeks` (Average playtime - last 2 weeks)
- **Type:** Integer (minutes)
- **Description:** Average playtime for players who played in the last 2 weeks
- **Why it matters:** Shows **current engagement** - which games are trending NOW
- **Database column:** Need to create: `avg_hours_2weeks`
- **Conversion needed:** Divide by 60 to convert minutes → hours

### 3. `median_2weeks` (Median playtime - last 2 weeks)
- **Type:** Integer (minutes)
- **Description:** Median playtime for players who played in the last 2 weeks
- **Why it matters:** Recent engagement without outlier skew
- **Database column:** Need to create: `median_hours_2weeks`
- **Conversion needed:** Divide by 60 to convert minutes → hours

### 4. `ccu` (Peak concurrent users)
- **Type:** Integer
- **Description:** Peak number of players online at the same time
- **Why it matters:** Shows game popularity and multiplayer health
- **Database column:** `ccu` (column exists but is NULL)
- **Conversion needed:** None - use as-is

### 5. `languages` (Supported languages)
- **Type:** String (comma-separated)
- **Description:** All languages the game supports
- **Why it matters:** International market reach - games with more languages = bigger potential audience
- **Database column:** Need to create: `supported_languages`
- **Conversion needed:** None - store as TEXT

### 6. `userscore` (User aggregate score)
- **Type:** Integer (0-100)
- **Description:** Overall user score calculated by SteamSpy
- **Why it matters:** Quick quality metric (0-100 scale)
- **Database column:** Need to create: `userscore`
- **Conversion needed:** None - use as-is

---

## 🔹 Complex Field (1 field)

### 7. `genre` (Game genres)
- **Type:** String (comma-separated)
- **Description:** Game genres like "Action, Free To Play"
- **Why it matters:** Genre analysis for market segmentation
- **Database column:** `genres` (column exists but is NULL)
- **Conversion needed:** None - store as TEXT
- **Note:** This is similar but NOT identical to Steam API genres

### 8. `tags` (User-generated tags with vote counts)
- **Type:** JSON object
- **Description:** User tags with popularity scores
- **Example:**
  ```json
  {
    "FPS": 91172,
    "Shooter": 65634,
    "Multiplayer": 62536,
    "Competitive": 53536
  }
  ```
- **Why it matters:** **EXTREMELY VALUABLE** - shows what players actually think about the game
- **Database column:** Need to create: `tags` (JSONB) or `top_tags` (TEXT)
- **Conversion needed:**
  - Option 1: Store entire JSON as JSONB
  - Option 2: Store top 5-10 tags as comma-separated TEXT

---

## Summary: What You're Missing

| SteamSpy Field | Your DB Column | Status | Value |
|----------------|----------------|--------|-------|
| `median_forever` | `median_hours_played` | Column exists, NULL | **HIGH** - Better than average |
| `average_2weeks` | Not created yet | Missing | **HIGH** - Recent engagement |
| `median_2weeks` | Not created yet | Missing | **HIGH** - Recent engagement |
| `ccu` | `ccu` | Column exists, NULL | **MEDIUM** - Popularity metric |
| `languages` | Not created yet | Missing | **MEDIUM** - Market reach |
| `userscore` | Not created yet | Missing | **LOW** - Redundant with rating % |
| `genre` | `genres` | Column exists, NULL | **HIGH** - Genre analysis |
| `tags` | Not created yet | Missing | **VERY HIGH** - Player sentiment |

---

## Recommended Action Plan

### Phase 1: Update `enrich_steam_data_fast.py` to fetch these 6 high-value fields:

1. ✅ `median_forever` → `median_hours_played` (column exists)
2. ✅ `ccu` → `ccu` (column exists)
3. ✅ `genre` → `genres` (column exists)
4. ✅ `average_2weeks` → `avg_hours_2weeks` (new column)
5. ✅ `median_2weeks` → `median_hours_2weeks` (new column)
6. ✅ `tags` → `top_tags` (new column - store top 10 as TEXT)

Skip these for now:
- ❌ `languages` - Can get better data from Steam API later
- ❌ `userscore` - Redundant with your calculated `rating_percentage`

---

## SQL to Add Missing Columns

```sql
ALTER TABLE steam_apps
ADD COLUMN IF NOT EXISTS avg_hours_2weeks NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS median_hours_2weeks NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS top_tags TEXT;

-- Also add to fact_game_metrics
ALTER TABLE fact_game_metrics
ADD COLUMN IF NOT EXISTS avg_hours_2weeks NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS median_hours_2weeks NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS top_tags TEXT;
```

---

## Updated `enrich_steam_data_fast.py` Changes Needed

### Current code (lines 57-69):
```python
result = {
    'appid': appid,
    'players_forever': safe_int(data.get('players_forever')),
    'average_forever': safe_int(data.get('average_forever')),
    'price': safe_int(data.get('price')),
    'initialprice': safe_int(data.get('initialprice')),
    'positive': safe_int(data.get('positive')),
    'negative': safe_int(data.get('negative')),
    'score_rank': safe_int(data.get('score_rank')),
    'developer': data.get('developer', 'Unknown') or 'Unknown',
    'publisher': data.get('publisher', 'Unknown') or 'Unknown'
}
```

### Updated code (add 6 new fields):
```python
# Extract top 10 tags as comma-separated string
tags_dict = data.get('tags', {})
top_tags = ', '.join([
    f"{tag}" for tag, count in
    sorted(tags_dict.items(), key=lambda x: x[1], reverse=True)[:10]
]) if tags_dict else ''

result = {
    'appid': appid,
    'players_forever': safe_int(data.get('players_forever')),
    'average_forever': safe_int(data.get('average_forever')),
    'median_forever': safe_int(data.get('median_forever')),        # NEW
    'average_2weeks': safe_int(data.get('average_2weeks')),        # NEW
    'median_2weeks': safe_int(data.get('median_2weeks')),          # NEW
    'ccu': safe_int(data.get('ccu')),                              # NEW
    'price': safe_int(data.get('price')),
    'initialprice': safe_int(data.get('initialprice')),
    'positive': safe_int(data.get('positive')),
    'negative': safe_int(data.get('negative')),
    'score_rank': safe_int(data.get('score_rank')),
    'developer': data.get('developer', 'Unknown') or 'Unknown',
    'publisher': data.get('publisher', 'Unknown') or 'Unknown',
    'genre': data.get('genre', '') or '',                          # NEW
    'top_tags': top_tags                                           # NEW
}
```

---

## Bottom Line

**You're missing 6 valuable SteamSpy fields:**

1. `median_forever` - Already have column, just need to populate ⭐⭐⭐
2. `ccu` - Already have column, just need to populate ⭐⭐
3. `genre` - Already have column as `genres`, just need to populate ⭐⭐⭐
4. `average_2weeks` - Need to create column ⭐⭐⭐
5. `median_2weeks` - Need to create column ⭐⭐⭐
6. `tags` - Need to create column ⭐⭐⭐⭐⭐ (MOST VALUABLE!)

**Would you like me to update your `enrich_steam_data_fast.py` script to fetch these 6 fields?**
