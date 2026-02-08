# PlayIntel ETL - Daily Data Refresh

Automated daily data refresh from SteamSpy and Steam API to Supabase.

## Dynamic Data Points Refreshed

All dynamic data points that change over time are refreshed on each run:

### From SteamSpy API (Primary Source)
| Field | Description | Change Frequency |
|-------|-------------|------------------|
| `total_owners` | Estimated owner count | Daily-Weekly |
| `avg_playtime` | Average playtime (forever) | Daily |
| `median_playtime` | Median playtime (forever) | Daily |
| `avg_playtime_2weeks` | Average playtime (last 2 weeks) | Very frequent |
| `median_playtime_2weeks` | Median playtime (last 2 weeks) | Very frequent |
| `positive_reviews` | Positive review count | Daily |
| `negative_reviews` | Negative review count | Daily |
| `ccu` | Current concurrent users | Very frequent |
| `score_rank` | SteamSpy ranking score | Daily |
| `price_cents` | Current price in cents | On sales/changes |
| `initialprice_cents` | Original price in cents | Rarely |
| `tags` | Top 10 community tags | Occasionally |
| `genre` | Game genres | Rarely |
| `developer` | Developer name | Rarely |
| `publisher` | Publisher name | Rarely |

### From Steam Official API (Secondary Source)
| Field | Description | Change Frequency |
|-------|-------------|------------------|
| `recommendations` | Total recommendations | Daily |
| `metacritic_score` | Metacritic score | Occasionally |
| `platform_windows` | Windows support | Rarely |
| `platform_mac` | Mac support | Occasionally |
| `platform_linux` | Linux support | Occasionally |
| `dlc_count` | Number of DLCs | On DLC release |
| `achievement_count` | Number of achievements | On updates |
| `language_count` | Supported languages | Occasionally |
| `required_age` | Age rating | Rarely |

### Refresh Strategy
- **New games**: Full refresh from both APIs
- **Top 100 popular games**: Full refresh including Steam API
- **Other existing games**: SteamSpy-only refresh (faster)

## Time Estimates Per Run

| Scenario | New Games | Enrichments | Total Time |
|----------|-----------|-------------|------------|
| **Quiet day** | 5-10 | 50-100 | ~15-20 min |
| **Normal day** | 20-50 | 100-200 | ~25-40 min |
| **Busy day** | 100+ | 500+ | ~60-90 min |
| **Initial backfill** | 500+ | 1000+ | ~2-3 hours |

### Breakdown by Step

1. **Fetch new games**: ~61 seconds per page (API rate limit)
   - Typical: 2-5 pages = 2-5 minutes
   - Max configured: 20 pages = ~20 minutes

2. **Enrich games**: ~0.25 seconds per game (4 concurrent)
   - 100 games = ~25 seconds actual, ~2 min with overhead
   - 1000 games = ~4 min actual, ~15 min with overhead

3. **Update analytics**: ~1-2 minutes (SQL operations)

## Setup Instructions

### 1. Add GitHub Secret

Go to your repository → Settings → Secrets and variables → Actions → New repository secret

- **Name**: `SUPABASE_DATABASE_URL`
- **Value**: Your Supabase connection string:
  ```
  postgresql://postgres.yrnlavhgbbhkvaxlhchp:[PASSWORD]@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
  ```

### 2. Enable GitHub Actions

The workflow is already configured in `.github/workflows/daily-refresh.yml`.

It runs automatically at **6 AM UTC daily** (adjust the cron in the file if needed).

### 3. Manual Trigger

You can also trigger manually:
1. Go to Actions tab in GitHub
2. Select "Daily Data Refresh"
3. Click "Run workflow"
4. Choose mode: `full`, `fetch-only`, `enrich-only`, or `analytics-only`

## Local Testing

```bash
# Set the environment variable
export DATABASE_URL="postgresql://postgres.xxx:password@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"

# Run full refresh
python etl/daily_refresh.py

# Or run specific steps
python etl/daily_refresh.py --fetch-only
python etl/daily_refresh.py --enrich-only
python etl/daily_refresh.py --analytics-only
```

## Cost Estimates

### GitHub Actions (Recommended)
- **Free tier**: 2,000 minutes/month
- **Daily 30-min run**: ~900 min/month = **Free**
- **If exceeded**: $0.008/minute = ~$7/month

### Alternative: Railway
- $5/month for cron jobs
- More reliable for long-running jobs

### Alternative: Local Cron
- Free but requires machine to be on
- Add to crontab: `0 6 * * * cd /path/to/playintel && python etl/daily_refresh.py`

## Monitoring

Check the GitHub Actions tab for:
- Run history
- Logs for each step
- Success/failure status

The script logs:
- Number of new games fetched
- Number of games enriched
- Total runtime

## Troubleshooting

### "Connection refused" or timeout
- Check if Supabase project is active (free tier pauses after inactivity)
- Verify the connection string is correct

### "Rate limited" by SteamSpy
- The script respects rate limits, but if you see this, increase delays
- SteamSpy allows ~4 requests/second for app details

### "No new games found"
- Normal if running daily - most days have few new releases
- The script is working correctly

### Workflow fails silently
- Check GitHub Actions logs
- Ensure `SUPABASE_DATABASE_URL` secret is set correctly
