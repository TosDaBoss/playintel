# PlayIntel Use Cases & Aggregate Tables Design

## Data Available (High & Medium Coverage)

### High Coverage (90%+) - 77,274 games
| Column | Coverage | Description |
|--------|----------|-------------|
| appid, name, developer, publisher | 100% | Identity |
| price_category | 100% | Free, Budget, Low, Medium, Standard, Premium, AAA |
| total_owners | 100% | Estimated ownership (SteamSpy) |
| positive_reviews, total_reviews | 96-99% | Review counts |
| rating_percentage, review_category | 96-100% | Rating metrics |
| genres, top_tags | 99.6% | Classification |

### Medium Coverage (20-90%)
| Column | Coverage | Games | Description |
|--------|----------|-------|-------------|
| price_usd | 87.2% | 67,402 | Current price |
| negative_reviews | 80.5% | 62,196 | Negative count |
| avg_hours_played | 27.0% | 20,848 | Playtime |
| engagement_score | 26.7% | 20,595 | Engagement metric |
| hours_per_dollar | 22.8% | 17,605 | Value metric |
| ccu | 21.2% | 16,359 | Peak concurrent |

---

## Use Cases & Questions They Answer

### 1. PRICING STRATEGY
**Questions:**
- "What should I price my roguelike at?"
- "What's the best price for a 2D platformer?"
- "Do higher-priced games get better ratings?"
- "What's the sweet spot price for my genre?"

**Data Needed:** price_usd, price_category, genres, top_tags, total_owners, rating_percentage

**Insights from Analysis:**
- Budget ($0-$5): 35,814 games, 43K avg owners, 75% rating
- Medium ($10-$20): 11,226 games, 182K avg owners, 77.5% rating
- Standard ($20-$30): 2,184 games, 430K avg owners, 76.4% rating
- AAA ($50+): 587 games, 1.1M avg owners, 63.1% rating (lower rating!)

---

### 2. GENRE/TAG MARKET ANALYSIS
**Questions:**
- "How saturated is the roguelike market?"
- "Which genres have the best success rate?"
- "What tags correlate with higher ratings?"
- "What's the competition for FPS games?"

**Data Needed:** genres, top_tags, total_owners, rating_percentage, price_category

**Insights from Analysis:**
- Indie: 55,020 games (most saturated)
- Action: 32,990 games
- Casual: 31,816 games
- RPG: 13,651 games
- 448 unique tags available

---

### 3. COMPETITIVE BENCHMARKING
**Questions:**
- "Who are my competitors in the horror survival space?"
- "How do similar games perform?"
- "What's the top game in my niche doing right?"
- "Show me games similar to Stardew Valley"

**Data Needed:** name, developer, genres, top_tags, total_owners, rating_percentage, price_usd

---

### 4. SUCCESS PROBABILITY / EXPECTATIONS
**Questions:**
- "What's a realistic owner count for a $15 indie RPG?"
- "What rating should I expect?"
- "What percentage of games reach 100K owners?"
- "What separates hits from failures?"

**Data Needed:** total_owners, rating_percentage, price_category, genres, review_category

**Insights from Analysis:**
- Mega (10M+): 97 games, $19.59 avg, 84.3% rating
- Hit (1M-10M): 1,353 games, $17.45 avg, 84.1% rating
- Success (100K-1M): 7,515 games, $10.67 avg, 78.2% rating
- Moderate (10K-100K): 68,309 games, $6.99 avg, 74.9% rating

---

### 5. REVIEW OPTIMIZATION
**Questions:**
- "What rating threshold should I aim for?"
- "What's the difference between Mostly Positive and Very Positive?"
- "How many reviews do I need to escape 'Insufficient Reviews'?"
- "Do certain genres get better reviews?"

**Data Needed:** rating_percentage, review_category, positive_reviews, negative_reviews, total_reviews, genres

**Insights from Analysis:**
- Overwhelmingly Positive: 7,012 games, 227K avg owners
- Very Positive: 20,335 games, 237K avg owners
- Mixed: 12,815 games, 141K avg owners
- Insufficient Reviews: 25,525 games, 15K avg owners

---

### 6. PLAYTIME & VALUE ANALYSIS
**Questions:**
- "What playtime should I target for a $20 game?"
- "What's the hours-per-dollar benchmark?"
- "Do longer games get better reviews?"
- "Free games vs paid - what's the playtime difference?"

**Data Needed:** avg_hours_played, hours_per_dollar, price_usd, rating_percentage

**Insights from Analysis:**
- Free: 14.6 hrs avg playtime, 72% rating
- $1-5: 1.1 hrs avg playtime
- $16-20: 6.3 hrs avg playtime
- $31-50: 24.7 hrs avg playtime

---

### 7. PUBLISHER/DEVELOPER INSIGHTS
**Questions:**
- "Who are the top indie developers?"
- "What's the average game count per successful developer?"
- "Which publishers dominate my genre?"

**Data Needed:** developer, publisher, total_owners, rating_percentage, genres

**Insights from Analysis:**
- 49,771 unique developers
- 1.6 avg games per developer
- Top: Valve (530M owners, 34 games, 87% rating)

---

### 8. FREE-TO-PLAY ANALYSIS
**Questions:**
- "Should I go free-to-play?"
- "How do F2P games compare to paid?"
- "What's the F2P success rate?"

**Data Needed:** is_free, total_owners, rating_percentage, avg_hours_played

**Insights from Analysis:**
- Free: 9,872 games, 294K avg owners, 72% rating, 14.6 hrs
- Paid: 67,402 games, 109K avg owners, 76% rating, 2.8 hrs

---

## Proposed Aggregate Tables

### Table 1: `agg_price_tier_stats`
Pre-computed stats by price tier for instant pricing questions.

```sql
CREATE TABLE agg_price_tier_stats (
    price_category VARCHAR(50) PRIMARY KEY,
    game_count INTEGER,
    avg_owners BIGINT,
    median_owners BIGINT,
    avg_rating DECIMAL(5,2),
    avg_playtime_hours DECIMAL(10,2),
    avg_hours_per_dollar DECIMAL(10,2),
    games_with_90plus_rating INTEGER,
    games_with_1m_plus_owners INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** Pricing strategy questions, price tier comparisons

---

### Table 2: `agg_genre_stats`
Stats by genre for market analysis.

```sql
CREATE TABLE agg_genre_stats (
    genre VARCHAR(100) PRIMARY KEY,
    game_count INTEGER,
    avg_owners BIGINT,
    median_owners BIGINT,
    avg_rating DECIMAL(5,2),
    avg_price DECIMAL(10,2),
    games_90plus_rating INTEGER,
    games_1m_plus_owners INTEGER,
    top_game_name VARCHAR(255),
    top_game_owners BIGINT,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** Genre saturation, genre success rates, market sizing

---

### Table 3: `agg_tag_stats`
Stats by Steam tag for niche analysis.

```sql
CREATE TABLE agg_tag_stats (
    tag VARCHAR(100) PRIMARY KEY,
    game_count INTEGER,
    avg_owners BIGINT,
    median_owners BIGINT,
    avg_rating DECIMAL(5,2),
    avg_price DECIMAL(10,2),
    games_90plus_rating INTEGER,
    games_1m_plus_owners INTEGER,
    best_price_tier VARCHAR(50),  -- Price tier with highest avg owners for this tag
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** Tag market analysis, niche identification, positioning

---

### Table 4: `agg_tag_price_matrix`
Cross-reference of tags and price tiers for optimal pricing by niche.

```sql
CREATE TABLE agg_tag_price_matrix (
    tag VARCHAR(100),
    price_category VARCHAR(50),
    game_count INTEGER,
    avg_owners BIGINT,
    avg_rating DECIMAL(5,2),
    success_rate DECIMAL(5,2),  -- % of games with 100K+ owners
    PRIMARY KEY (tag, price_category),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** "What should I price my roguelike at?" with specific data

---

### Table 5: `agg_review_tier_stats`
Stats by review category for expectation setting.

```sql
CREATE TABLE agg_review_tier_stats (
    review_category VARCHAR(50) PRIMARY KEY,
    min_rating DECIMAL(5,2),
    max_rating DECIMAL(5,2),
    game_count INTEGER,
    avg_owners BIGINT,
    avg_reviews INTEGER,
    avg_price DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** Review threshold questions, rating expectations

---

### Table 6: `agg_ownership_tier_stats`
Stats by ownership bracket for success benchmarking.

```sql
CREATE TABLE agg_ownership_tier_stats (
    ownership_tier VARCHAR(50) PRIMARY KEY,  -- 'Mega', 'Hit', 'Success', 'Moderate', 'Small'
    min_owners BIGINT,
    max_owners BIGINT,
    game_count INTEGER,
    avg_rating DECIMAL(5,2),
    avg_price DECIMAL(10,2),
    avg_playtime DECIMAL(10,2),
    pct_of_total DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** Success probability, realistic expectations

---

### Table 7: `agg_developer_stats`
Developer performance stats.

```sql
CREATE TABLE agg_developer_stats (
    developer VARCHAR(255) PRIMARY KEY,
    game_count INTEGER,
    total_owners BIGINT,
    avg_owners_per_game BIGINT,
    avg_rating DECIMAL(5,2),
    best_game_name VARCHAR(255),
    best_game_owners BIGINT,
    primary_genre VARCHAR(100),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** Developer benchmarking, competitor analysis

---

### Table 8: `agg_genre_price_performance`
Best price points by genre.

```sql
CREATE TABLE agg_genre_price_performance (
    genre VARCHAR(100),
    price_category VARCHAR(50),
    game_count INTEGER,
    avg_owners BIGINT,
    avg_rating DECIMAL(5,2),
    success_rate DECIMAL(5,2),
    PRIMARY KEY (genre, price_category),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Powers:** Genre-specific pricing recommendations

---

## Sample Queries These Tables Enable

### Q: "What should I price my roguelike at?"
```sql
SELECT price_category, game_count, avg_owners, avg_rating, success_rate
FROM agg_tag_price_matrix
WHERE tag = 'Roguelike'
ORDER BY avg_owners DESC;
```

### Q: "How saturated is the horror genre?"
```sql
SELECT game_count, avg_owners, games_1m_plus_owners,
       ROUND(games_1m_plus_owners::decimal / game_count * 100, 2) as hit_rate
FROM agg_genre_stats
WHERE genre = 'Horror';
```

### Q: "What's realistic for my game?"
```sql
SELECT ownership_tier, game_count, pct_of_total, avg_rating, avg_price
FROM agg_ownership_tier_stats
ORDER BY min_owners DESC;
```

### Q: "Who are the top indie RPG developers?"
```sql
SELECT developer, game_count, total_owners, avg_rating
FROM agg_developer_stats
WHERE primary_genre = 'RPG'
ORDER BY total_owners DESC
LIMIT 10;
```

---

## Implementation Priority

### Phase 1 (Core - Immediate Value)
1. `agg_price_tier_stats` - Powers pricing questions
2. `agg_tag_stats` - Powers niche analysis
3. `agg_ownership_tier_stats` - Powers expectations

### Phase 2 (Enhanced Analysis)
4. `agg_tag_price_matrix` - Specific pricing by niche
5. `agg_genre_stats` - Genre market analysis
6. `agg_review_tier_stats` - Review expectations

### Phase 3 (Advanced)
7. `agg_developer_stats` - Competitor analysis
8. `agg_genre_price_performance` - Genre-specific pricing

---

## Refresh Strategy

These tables should be refreshed:
- **Daily**: Not needed (game data doesn't change that fast)
- **Weekly**: Recommended for active development
- **On-demand**: After any data enrichment run

Add a `last_refreshed` table to track refresh timestamps.
