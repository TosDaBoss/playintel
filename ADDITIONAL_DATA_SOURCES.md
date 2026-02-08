# Additional Data Sources for Steam Market Analysis

## Steam Official API - Available Fields

### ✅ Currently Using (7 fields)
From: `https://store.steampowered.com/api/appdetails?appids={appid}`

1. **name** - Game title
2. **type** - App type (game, dlc, software)
3. **developers** - Developer list
4. **publishers** - Publisher list
5. **is_free** - Free-to-play status
6. **price_overview** - Price and discount info
7. **release_date** - Release date

### ❌ NOT Using - HIGH VALUE Fields

#### 1. **recommendations** (VERY HIGH VALUE) ⭐⭐⭐⭐⭐
```json
{
  "total": 4872789
}
```
- **What it is:** Total number of "thumbs up" recommendations on Steam
- **Why valuable:** Strong quality signal - more reliable than just reviews
- **Use cases:**
  - "Show me games with >100k recommendations"
  - "What's the recommendation-to-owner ratio?" (virality metric)
- **Database column:** `recommendations` (INTEGER)

#### 2. **metacritic** (HIGH VALUE) ⭐⭐⭐⭐
```json
{
  "score": 83,
  "url": "https://www.metacritic.com/game/counter-strike-2"
}
```
- **What it is:** Metacritic critic score (0-100)
- **Why valuable:** Professional critic opinion vs user opinion
- **Use cases:**
  - "Compare metacritic vs user ratings"
  - "Show games where critics loved it but users didn't" (overrated analysis)
- **Database columns:** `metacritic_score` (INTEGER), `metacritic_url` (TEXT)

#### 3. **platforms** (HIGH VALUE) ⭐⭐⭐⭐
```json
{
  "windows": true,
  "mac": false,
  "linux": true
}
```
- **What it is:** Supported platforms
- **Why valuable:** Cross-platform games have wider market reach
- **Use cases:**
  - "Show Mac-compatible indie games"
  - "What percentage of top games support Linux?"
- **Database columns:** `platform_windows`, `platform_mac`, `platform_linux` (BOOLEAN)

#### 4. **supported_languages** (MEDIUM VALUE) ⭐⭐⭐
```
"English<strong>*</strong>, French, German, Spanish..."
```
- **What it is:** List of supported languages (* = full audio)
- **Why valuable:** International market reach indicator
- **Use cases:**
  - "Show games with Chinese localization"
  - "Average owners for games with 10+ languages vs 1 language"
- **Database column:** `supported_languages` (TEXT) or `language_count` (INTEGER)

#### 5. **dlc** (MEDIUM VALUE) ⭐⭐⭐
```json
[2678630, 2678631, 2678632]
```
- **What it is:** List of DLC app IDs
- **Why valuable:** Post-launch monetization indicator
- **Use cases:**
  - "Games with most DLC packages"
  - "Average DLC count for successful indie games"
- **Database column:** `dlc_count` (INTEGER)

#### 6. **achievements** (MEDIUM VALUE) ⭐⭐⭐
```json
{
  "total": 167
}
```
- **What it is:** Total achievement count
- **Why valuable:** Engagement/replayability indicator
- **Use cases:**
  - "Do achievement-rich games have higher playtime?"
  - "Optimal achievement count for indie games"
- **Database column:** `achievement_count` (INTEGER)

#### 7. **required_age** (LOW VALUE) ⭐⭐
```json
0  // or 18, 21, etc.
```
- **What it is:** Age rating (ESRB/PEGI)
- **Why valuable:** Market segmentation
- **Use cases:**
  - "Family-friendly games (required_age = 0)"
  - "Mature game performance analysis"
- **Database column:** `required_age` (INTEGER)

#### 8. **screenshots** & **movies** (LOW VALUE) ⭐
```json
{
  "screenshots": [{"id": 0, "path_full": "url"}, ...],
  "movies": [{"id": 256, "webm": {"480": "url"}}, ...]
}
```
- **What it is:** Count of screenshots and trailers
- **Why valuable:** Marketing effort indicator
- **Use cases:**
  - "Do more screenshots correlate with sales?"
- **Database columns:** `screenshot_count`, `trailer_count` (INTEGER)

#### 9. **controller_support** (LOW VALUE) ⭐
```
"full" / "partial" / null
```
- **What it is:** Controller support level
- **Why valuable:** Accessibility/platform indicator
- **Database column:** `controller_support` (TEXT)

#### 10. **content_descriptors** (LOW VALUE) ⭐
```json
{
  "ids": [2, 5],
  "notes": "Includes intense violence and blood"
}
```
- **What it is:** Mature content warnings
- **Why valuable:** Content moderation flags
- **Database column:** `has_violence`, `has_nudity` (BOOLEAN)

#### 11. **short_description** (SPECIAL USE) 💡
```
"For over two decades, Counter-Strike has offered an elite competitive experience..."
```
- **What it is:** Brief marketing description (300 chars)
- **Why valuable:** Semantic search, AI analysis
- **Use cases:**
  - "Find games similar to X" (vector embeddings)
  - "Categorize games by description themes"
- **Database column:** `description` (TEXT)

---

## Other Steam API Endpoints

### 1. Steam Reviews API ⭐⭐⭐⭐
`https://store.steampowered.com/appreviews/{appid}?json=1`

**Available data:**
- Review text and ratings
- Helpful/funny vote counts
- Purchase type (Steam vs key)
- Playtime at review time
- Language of review

**High-value metrics:**
- **Sentiment analysis** - Analyze what players actually say
- **Review velocity** - Reviews per day (trending indicator)
- **Key activation ratio** - Steam purchase vs external key (fraud indicator)

**Database additions:**
- `review_velocity` (NUMERIC) - Recent review rate
- `steam_purchase_ratio` (NUMERIC) - % bought on Steam

### 2. Steam Spy - Additional Endpoints

#### `/top100in2weeks` & `/top100forever`
- Pre-filtered trending/all-time lists
- Faster than querying all games

#### `/genre` endpoint
`https://steamspy.com/api.php?request=genre&genre=Action`
- All games in a genre
- Genre-wide statistics

#### `/all` endpoint (paginated)
- Already using this in `steam_to_postgres.py`
- Returns 1000 games per page

---

## Third-Party Data Sources

### 1. **SteamDB.info** (No Public API) ❌
- Historical pricing data
- Player count graphs
- Regional pricing
- **Access:** Web scraping only (against ToS for commercial use)

### 2. **Steam Charts** (No Public API) ⭐⭐⭐
`https://steamcharts.com`
- Historical concurrent player data
- Peak player tracking
- **Access:** Web scraping (limited use okay)
- **Value:** Track player count trends over time

**Potential data:**
- `peak_players_30d` (INTEGER)
- `avg_players_30d` (INTEGER)
- `player_trend` (TEXT) - "rising" / "falling" / "stable"

### 3. **IGDB (Internet Game Database)** ⭐⭐⭐⭐
`https://api.igdb.com/v4/`
- **Status:** Free API (requires Twitch account)
- **Data:** Genres, themes, keywords, cover art, similar games
- **Value:** Better genre classification than Steam

**Potential enrichment:**
- More detailed genre taxonomy
- Theme tags (e.g., "Survival", "Horror")
- Similar game recommendations

### 4. **Reddit API** ⭐⭐⭐
`https://www.reddit.com/r/gamedev.json`
- **Status:** Free API
- **Data:** Community discussions, sentiment
- **Value:** Identify trending indie games early

**Potential metrics:**
- `reddit_mentions` (INTEGER)
- `reddit_sentiment` (NUMERIC)

### 5. **Twitch API** ⭐⭐⭐⭐⭐
`https://api.twitch.tv/helix/games`
- **Status:** Free API (requires app registration)
- **Data:**
  - Current viewer count
  - Top streamers
  - Total hours watched
- **Value:** **EXTREMELY HIGH** - Twitch viewership = marketing reach

**Potential additions:**
- `twitch_viewers` (INTEGER) - Current viewers
- `twitch_hours_watched` (BIGINT) - Total watch time
- `twitch_streamer_count` (INTEGER)

### 6. **YouTube Gaming API** ⭐⭐⭐
- Similar to Twitch but for YouTube
- Video count, view count for game-related content

### 7. **OpenCritic** ⭐⭐⭐
`https://api.opencritic.com/`
- **Status:** Free for non-commercial
- **Data:** Aggregated critic reviews
- **Value:** Alternative to Metacritic

---

## Recommended Next Steps - Priority Order

### Phase 1: Steam Official API (Easy) ⭐⭐⭐⭐⭐
**Add these 5 high-value fields:**
1. ✅ `recommendations` - Quality signal
2. ✅ `metacritic_score` - Critic opinion
3. ✅ `platforms` (windows/mac/linux) - Market reach
4. ✅ `dlc_count` - Monetization indicator
5. ✅ `achievement_count` - Engagement indicator

**Effort:** Low - Same API you're already using
**Impact:** High - Strong quality/market signals

### Phase 2: Twitch API (Medium) ⭐⭐⭐⭐⭐
**Add streaming data:**
1. ✅ `twitch_viewers` - Current popularity
2. ✅ `twitch_hours_watched` - Total viewership

**Effort:** Medium - New API, requires registration
**Impact:** VERY HIGH - Streaming = marketing reach = sales

### Phase 3: Steam Reviews API (Medium) ⭐⭐⭐⭐
**Add review analytics:**
1. ✅ `review_velocity` - Trending indicator
2. ✅ `steam_purchase_ratio` - Legitimacy metric

**Effort:** Medium - New endpoint, need to process review data
**Impact:** High - Detect trending games early

### Phase 4: IGDB (Optional) ⭐⭐⭐
**Better game classification:**
1. ✅ Improved genre taxonomy
2. ✅ Theme tags
3. ✅ Similar games

**Effort:** Medium - New API integration
**Impact:** Medium - Better categorization for recommendations

---

## Estimated Storage Impact

| Data Source | New Columns | Storage per Game | Total for 5K games |
|-------------|-------------|------------------|--------------------|
| Steam API (Phase 1) | 5 | ~50 bytes | 250 KB |
| Twitch API (Phase 2) | 2 | ~20 bytes | 100 KB |
| Steam Reviews (Phase 3) | 2 | ~20 bytes | 100 KB |
| IGDB (Phase 4) | 3 | ~200 bytes | 1 MB |
| **TOTAL** | **12** | **~290 bytes** | **~1.5 MB** |

**Conclusion:** Negligible storage impact - go for it!

---

## Quick Implementation Estimate

### Phase 1: Steam API Fields (RECOMMENDED START HERE)
- **Time to implement:** 2-3 hours
- **Script changes:** Update `enrich_steam_data_fast.py` to fetch 5 more fields
- **Database changes:** Add 5 columns to `steam_apps` and `fact_game_metrics`
- **Re-run time:** ~20 minutes (same enrichment script)

### Script modification needed:
```python
# In fetch_app_details_async, add:
'recommendations': steam_data.get('recommendations', {}).get('total', 0),
'metacritic_score': steam_data.get('metacritic', {}).get('score', None),
'platform_windows': steam_data.get('platforms', {}).get('windows', False),
'platform_mac': steam_data.get('platforms', {}).get('mac', False),
'platform_linux': steam_data.get('platforms', {}).get('linux', False),
'dlc_count': len(steam_data.get('dlc', [])),
'achievement_count': steam_data.get('achievements', {}).get('total', 0),
```

**Want me to implement Phase 1 for you?**
