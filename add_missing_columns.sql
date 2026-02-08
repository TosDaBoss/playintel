-- Add missing columns to fact_game_metrics table

ALTER TABLE fact_game_metrics
ADD COLUMN IF NOT EXISTS release_date TEXT,
ADD COLUMN IF NOT EXISTS genres TEXT,
ADD COLUMN IF NOT EXISTS categories TEXT,
ADD COLUMN IF NOT EXISTS median_hours_played NUMERIC,
ADD COLUMN IF NOT EXISTS ccu INTEGER;

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_total_owners ON fact_game_metrics(total_owners DESC);
CREATE INDEX IF NOT EXISTS idx_avg_hours_played ON fact_game_metrics(avg_hours_played DESC);
CREATE INDEX IF NOT EXISTS idx_developer ON fact_game_metrics(developer);
CREATE INDEX IF NOT EXISTS idx_genres ON fact_game_metrics(genres);
CREATE INDEX IF NOT EXISTS idx_release_date ON fact_game_metrics(release_date);

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'fact_game_metrics'
ORDER BY ordinal_position;
