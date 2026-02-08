# PlayIntel Data Columns Reference

## Current Database Schema (27 columns)

### ✅ Currently Populated
1. `appid` - Unique Steam app ID (NOT NULL)
2. `name` - Game name
3. `developer` - Developer name(s)
4. `publisher` - Publisher name(s)
5. `price_usd` - Current price in USD
6. `initialprice_usd` - Original launch price
7. `is_free` - Boolean: is the game free-to-play
8. `has_discount` - Boolean: currently on sale
9. `discount_percentage` - Current discount %
10. `price_category` - Price range category (e.g., "Budget", "Premium")
11. `positive_reviews` - Count of positive reviews
12. `negative_reviews` - Count of negative reviews
13. `total_reviews` - Total review count
14. `rating_percentage` - % positive reviews
15. `review_category` - Rating category (e.g., "Very Positive")
16. `engagement_score` - Calculated engagement metric
17. `score_rank` - Ranking by score
18. `created_at` - Record creation timestamp
19. `updated_at` - Record update timestamp

### ⚠️ Currently NULL/Empty (Need SteamSpy/Steam API)
20. `total_owners` - **Estimated owner count (SteamSpy)**
21. `avg_hours_played` - **Average playtime in hours (SteamSpy)**
22. `median_hours_played` - **Median playtime in hours (SteamSpy)**
23. `ccu` - **Peak concurrent users (SteamSpy)**
24. `hours_per_dollar` - Calculated: avg_hours / price
25. `release_date` - **Game release date (Steam API)**
26. `genres` - **Game genres (Steam API)**
27. `categories` - **Game categories (Steam API)**

---

## SteamSpy API - All Available Fields

### 🔹 Currently Using (8 fields)
```json
{
  "appid": 730,
  "name": "Counter-Strike 2",
  "developer": "Valve",
  "publisher": "Valve",
  "owners": "100,000,000 .. 200,000,000",      // → total_owners (parsed)
  "average_forever": 32997,                     // → avg_hours_played (minutes → hours)
  "median_forever": 6538,                       // → median_hours_played (minutes → hours)
  "ccu": 1013936                                // → ccu
}
```

### 🔹 Available but NOT Using (10 fields)
```json
{
  "positive": 7642084,                          // ✅ Already have (positive_reviews)
  "negative": 1173003,                          // ✅ Already have (negative_reviews)
  "userscore": 0,                               // Meta/user aggregate score (0-100)
  "average_2weeks": 688,                        // Avg playtime last 2 weeks (minutes)
  "median_2weeks": 290,                         // Median playtime last 2 weeks (minutes)
  "price": "0",                                 // ✅ Already have (price_usd)
  "initialprice": "0",                          // ✅ Already have (initialprice_usd)
  "discount": "0",                              // ✅ Already have (discount_percentage)
  "score_rank": "",                             // Overall ranking
  "languages": "English, Czech, Danish..."      // Supported languages
}
```

### 🔹 Complex Fields (2 fields)
```json
{
  "genre": "Action, Free To Play",              // Comma-separated genres
  "tags": {                                     // User-generated tags with vote counts
    "FPS": 91172,
    "Shooter": 65634,
    "Multiplayer": 62536,
    ...
  }
}
```

---

## Steam Official API - All Available Fields

### 🔹 Currently Using (5 fields)
```json
{
  "steam_appid": 730,
  "name": "Counter-Strike 2",
  "type": "game",                               // Filter: only keep "game" type
  "developers": ["Valve"],                      // → developer
  "publishers": ["Valve"],                      // → publisher
  "release_date": {
    "coming_soon": false,
    "date": "21 Aug, 2012"                      // → release_date
  },
  "is_free": true,                              // → is_free
  "price_overview": {
    "final": 0,                                 // → price_usd (in cents)
    "initial": 0,                               // → initialprice_usd
    "discount_percent": 0                       // → discount_percentage
  },
  "genres": [                                   // → genres (joined)
    {"id": "1", "description": "Action"},
    {"id": "37", "description": "Free To Play"}
  ],
  "categories": [                               // → categories (joined)
    {"id": 2, "description": "Single-player"},
    {"id": 1, "description": "Multi-player"}
  ]
}
```

### 🔹 Available but NOT Using (20+ fields)

#### Game Content
- `short_description` - Brief game description (1-2 sentences)
- `detailed_description` - Full HTML description
- `about_the_game` - Marketing description
- `supported_languages` - List of supported languages
- `header_image` - URL to header image
- `background` - URL to background image
- `screenshots` - Array of screenshot URLs
- `movies` - Array of trailer video URLs

#### Game Metadata
- `required_age` - ESRB/age rating (integer)
- `dlc` - Array of DLC app IDs
- `packages` - Array of package IDs
- `package_groups` - Pricing/bundle info
- `platforms` - {"windows": true, "mac": false, "linux": true}
- `metacritic` - Metacritic score and URL (if available)
- `achievements` - Achievement data
- `recommendations` - {"total": 4872789} - recommendation count

#### Requirements
- `pc_requirements` - PC system requirements (HTML)
- `mac_requirements` - Mac system requirements
- `linux_requirements` - Linux system requirements

#### Other
- `website` - Official game website URL
- `support_info` - Support URL and email
- `content_descriptors` - Violence/mature content warnings
- `ratings` - Regional ratings (ESRB, PEGI, etc.)

---

## Recommended Columns to Add

### High Value (Should Add)

1. **`average_2weeks`** (from SteamSpy)
   - Average playtime in last 2 weeks (recent engagement)
   - Useful for identifying trending/active games

2. **`median_2weeks`** (from SteamSpy)
   - Median playtime in last 2 weeks
   - Better metric than average (less skewed)

3. **`tags`** (from SteamSpy)
   - User-generated tags with vote counts
   - Store as JSON or top 5 tags as text
   - Extremely useful for genre analysis

4. **`supported_languages`** (from Steam API)
   - Shows market reach potential
   - Important for indie devs targeting international markets

5. **`platforms`** (from Steam API)
   - Windows/Mac/Linux support
   - Store as JSON: {"windows": true, "mac": false, "linux": true}

6. **`recommendations`** (from Steam API)
   - Total recommendation count
   - Strong signal of game quality/popularity

7. **`required_age`** (from Steam API)
   - Age rating
   - Useful for market segmentation

8. **`short_description`** (from Steam API)
   - Brief marketing pitch
   - Could enable semantic search later

### Medium Value (Nice to Have)

9. **`metacritic_score`** (from Steam API)
   - Critics' aggregate score
   - Not all games have this

10. **`dlc_count`** (from Steam API)
    - Number of DLC packages
    - Indicates post-launch monetization

11. **`screenshot_count`** (from Steam API)
    - Number of screenshots
    - Could indicate polish/marketing effort

12. **`video_count`** (from Steam API)
    - Number of trailers
    - Marketing indicator

### Low Value (Skip for Now)

- HTML descriptions (too large, not queryable)
- System requirements (messy HTML, not structured)
- Image URLs (not useful for analytics)
- Support info (not useful for market analysis)

---

## Updated ETL Script Coverage

### What the new `etl_steam_data.py` pulls:

✅ **From SteamSpy:**
- `total_owners` (parsed from range)
- `avg_hours_played` (converted to hours)
- `median_hours_played` (converted to hours)
- `ccu` (peak concurrent users)

✅ **From Steam API:**
- `release_date`
- `genres` (comma-separated)
- `categories` (comma-separated)
- `developer`
- `publisher`
- `is_free`
- `price_usd`

### What it's NOT pulling (but could):

❌ **From SteamSpy:**
- `average_2weeks`
- `median_2weeks`
- `tags` (JSON object)
- `languages`
- `userscore`

❌ **From Steam API:**
- `supported_languages`
- `platforms`
- `recommendations`
- `required_age`
- `short_description`
- `metacritic`
- `dlc` array
- `screenshots`
- `movies`

---

## Summary

**Current Database:** 27 columns
**Currently Populated:** 19 columns (70%)
**Currently NULL:** 8 columns (30%) - need ETL script to fix

**SteamSpy offers:** 18 fields total
- Using: 8 fields (44%)
- Available: 10 more fields

**Steam API offers:** 30+ fields
- Using: 7 fields (23%)
- Available: 20+ more fields

**Recommendation:** Run the ETL script to populate the 8 NULL columns first, then decide if you want to add more columns based on analysis needs.
