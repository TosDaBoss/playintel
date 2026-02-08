-- PlayIntel Aggregate Tables
-- Run this script to create and populate aggregate tables for fast querying

-- ============================================================================
-- TABLE 1: Price Tier Statistics
-- ============================================================================
DROP TABLE IF EXISTS agg_price_tier_stats;

CREATE TABLE agg_price_tier_stats (
    price_category VARCHAR(50) PRIMARY KEY,
    sort_order INTEGER,
    game_count INTEGER,
    avg_owners BIGINT,
    median_owners BIGINT,
    avg_rating DECIMAL(5,2),
    avg_playtime_hours DECIMAL(10,2),
    avg_hours_per_dollar DECIMAL(10,2),
    games_90plus_rating INTEGER,
    games_1m_plus_owners INTEGER,
    success_rate_100k DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO agg_price_tier_stats
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
    ROUND(AVG(total_owners)) as avg_owners,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_owners)::BIGINT as median_owners,
    ROUND(AVG(rating_percentage)::numeric, 2) as avg_rating,
    ROUND(AVG(avg_hours_played)::numeric, 2) as avg_playtime_hours,
    ROUND(AVG(hours_per_dollar)::numeric, 2) as avg_hours_per_dollar,
    COUNT(*) FILTER (WHERE rating_percentage >= 90) as games_90plus_rating,
    COUNT(*) FILTER (WHERE total_owners >= 1000000) as games_1m_plus_owners,
    ROUND(COUNT(*) FILTER (WHERE total_owners >= 100000)::decimal / COUNT(*) * 100, 2) as success_rate_100k,
    NOW() as updated_at
FROM fact_game_metrics
WHERE price_category IS NOT NULL
GROUP BY price_category;

-- ============================================================================
-- TABLE 2: Tag Statistics (Top 100 tags)
-- ============================================================================
DROP TABLE IF EXISTS agg_tag_stats;

CREATE TABLE agg_tag_stats (
    tag VARCHAR(100) PRIMARY KEY,
    game_count INTEGER,
    avg_owners BIGINT,
    median_owners BIGINT,
    avg_rating DECIMAL(5,2),
    avg_price DECIMAL(10,2),
    games_90plus_rating INTEGER,
    games_1m_plus_owners INTEGER,
    success_rate_100k DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- This requires a function to parse tags - we'll populate via Python

-- ============================================================================
-- TABLE 3: Ownership Tier Statistics
-- ============================================================================
DROP TABLE IF EXISTS agg_ownership_tier_stats;

CREATE TABLE agg_ownership_tier_stats (
    ownership_tier VARCHAR(50) PRIMARY KEY,
    sort_order INTEGER,
    min_owners BIGINT,
    max_owners BIGINT,
    game_count INTEGER,
    avg_rating DECIMAL(5,2),
    avg_price DECIMAL(10,2),
    avg_playtime DECIMAL(10,2),
    pct_of_total DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO agg_ownership_tier_stats
WITH totals AS (SELECT COUNT(*) as total FROM fact_game_metrics)
SELECT
    CASE
        WHEN total_owners >= 10000000 THEN 'Mega (10M+)'
        WHEN total_owners >= 1000000 THEN 'Hit (1M-10M)'
        WHEN total_owners >= 100000 THEN 'Success (100K-1M)'
        WHEN total_owners >= 10000 THEN 'Moderate (10K-100K)'
        ELSE 'Small (<10K)'
    END as ownership_tier,
    CASE
        WHEN total_owners >= 10000000 THEN 1
        WHEN total_owners >= 1000000 THEN 2
        WHEN total_owners >= 100000 THEN 3
        WHEN total_owners >= 10000 THEN 4
        ELSE 5
    END as sort_order,
    MIN(total_owners) as min_owners,
    MAX(total_owners) as max_owners,
    COUNT(*) as game_count,
    ROUND(AVG(rating_percentage)::numeric, 2) as avg_rating,
    ROUND(AVG(price_usd)::numeric, 2) as avg_price,
    ROUND(AVG(avg_hours_played)::numeric, 2) as avg_playtime,
    ROUND(COUNT(*)::decimal / (SELECT total FROM totals) * 100, 2) as pct_of_total,
    NOW() as updated_at
FROM fact_game_metrics
GROUP BY 1, 2;

-- ============================================================================
-- TABLE 4: Review Category Statistics
-- ============================================================================
DROP TABLE IF EXISTS agg_review_tier_stats;

CREATE TABLE agg_review_tier_stats (
    review_category VARCHAR(50) PRIMARY KEY,
    sort_order INTEGER,
    min_rating DECIMAL(5,2),
    max_rating DECIMAL(5,2),
    game_count INTEGER,
    avg_owners BIGINT,
    avg_reviews INTEGER,
    avg_price DECIMAL(10,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO agg_review_tier_stats
SELECT
    review_category,
    CASE review_category
        WHEN 'Overwhelmingly Positive' THEN 1
        WHEN 'Very Positive' THEN 2
        WHEN 'Mostly Positive' THEN 3
        WHEN 'Mixed' THEN 4
        WHEN 'Mostly Negative' THEN 5
        WHEN 'Negative' THEN 6
        WHEN 'Overwhelmingly Negative' THEN 7
        WHEN 'Insufficient Reviews' THEN 8
        ELSE 9
    END as sort_order,
    MIN(rating_percentage) as min_rating,
    MAX(rating_percentage) as max_rating,
    COUNT(*) as game_count,
    ROUND(AVG(total_owners)) as avg_owners,
    ROUND(AVG(total_reviews)) as avg_reviews,
    ROUND(AVG(price_usd)::numeric, 2) as avg_price,
    NOW() as updated_at
FROM fact_game_metrics
WHERE review_category IS NOT NULL
GROUP BY review_category;

-- ============================================================================
-- TABLE 5: Genre Statistics
-- ============================================================================
DROP TABLE IF EXISTS agg_genre_stats;

CREATE TABLE agg_genre_stats (
    genre VARCHAR(100) PRIMARY KEY,
    game_count INTEGER,
    avg_owners BIGINT,
    median_owners BIGINT,
    avg_rating DECIMAL(5,2),
    avg_price DECIMAL(10,2),
    games_90plus_rating INTEGER,
    games_1m_plus_owners INTEGER,
    success_rate_100k DECIMAL(5,2),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Populated via Python (requires parsing comma-separated genres)

-- ============================================================================
-- TABLE 6: Tag + Price Matrix
-- ============================================================================
DROP TABLE IF EXISTS agg_tag_price_matrix;

CREATE TABLE agg_tag_price_matrix (
    tag VARCHAR(100),
    price_category VARCHAR(50),
    game_count INTEGER,
    avg_owners BIGINT,
    avg_rating DECIMAL(5,2),
    success_rate_100k DECIMAL(5,2),
    PRIMARY KEY (tag, price_category),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Populated via Python (requires parsing tags)

-- ============================================================================
-- TABLE 7: Developer Statistics (developers with 3+ games)
-- ============================================================================
DROP TABLE IF EXISTS agg_developer_stats;

CREATE TABLE agg_developer_stats (
    developer VARCHAR(255) PRIMARY KEY,
    game_count INTEGER,
    total_owners BIGINT,
    avg_owners_per_game BIGINT,
    avg_rating DECIMAL(5,2),
    best_game_name VARCHAR(255),
    best_game_owners BIGINT,
    primary_genres TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO agg_developer_stats
WITH dev_best_games AS (
    SELECT DISTINCT ON (developer)
        developer,
        name as best_game_name,
        total_owners as best_game_owners
    FROM fact_game_metrics
    WHERE developer IS NOT NULL AND developer <> ''
    ORDER BY developer, total_owners DESC
)
SELECT
    f.developer,
    COUNT(*) as game_count,
    SUM(f.total_owners) as total_owners,
    ROUND(AVG(f.total_owners)) as avg_owners_per_game,
    ROUND(AVG(f.rating_percentage)::numeric, 2) as avg_rating,
    b.best_game_name,
    b.best_game_owners,
    MODE() WITHIN GROUP (ORDER BY f.genres) as primary_genres,
    NOW() as updated_at
FROM fact_game_metrics f
JOIN dev_best_games b ON f.developer = b.developer
WHERE f.developer IS NOT NULL AND f.developer <> ''
GROUP BY f.developer, b.best_game_name, b.best_game_owners
HAVING COUNT(*) >= 3;

-- ============================================================================
-- TABLE 8: Genre + Price Performance
-- ============================================================================
DROP TABLE IF EXISTS agg_genre_price_performance;

CREATE TABLE agg_genre_price_performance (
    genre VARCHAR(100),
    price_category VARCHAR(50),
    game_count INTEGER,
    avg_owners BIGINT,
    avg_rating DECIMAL(5,2),
    success_rate_100k DECIMAL(5,2),
    PRIMARY KEY (genre, price_category),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Populated via Python (requires parsing genres)

-- ============================================================================
-- METADATA TABLE: Track refresh times
-- ============================================================================
DROP TABLE IF EXISTS agg_refresh_log;

CREATE TABLE agg_refresh_log (
    table_name VARCHAR(100) PRIMARY KEY,
    last_refreshed TIMESTAMP,
    row_count INTEGER,
    refresh_duration_seconds DECIMAL(10,2)
);

INSERT INTO agg_refresh_log (table_name, last_refreshed, row_count)
VALUES
    ('agg_price_tier_stats', NOW(), (SELECT COUNT(*) FROM agg_price_tier_stats)),
    ('agg_ownership_tier_stats', NOW(), (SELECT COUNT(*) FROM agg_ownership_tier_stats)),
    ('agg_review_tier_stats', NOW(), (SELECT COUNT(*) FROM agg_review_tier_stats)),
    ('agg_developer_stats', NOW(), (SELECT COUNT(*) FROM agg_developer_stats));

-- Show results
SELECT '✅ Created agg_price_tier_stats' as status, COUNT(*) as rows FROM agg_price_tier_stats
UNION ALL
SELECT '✅ Created agg_ownership_tier_stats', COUNT(*) FROM agg_ownership_tier_stats
UNION ALL
SELECT '✅ Created agg_review_tier_stats', COUNT(*) FROM agg_review_tier_stats
UNION ALL
SELECT '✅ Created agg_developer_stats', COUNT(*) FROM agg_developer_stats;
