# PlayIntel MCP – build plan for Claude Code

Hand this file to Claude Code from the repo root:

```
claude "Read MCP_BUILD_PLAN.md and work through it with me, one phase at a time. Stop at every [YOU] step and wait for me."
```

Steps marked **[YOU]** need the owner's accounts (Supabase, hosting, Stripe) or a decision.
Claude Code should never print secrets, commit `.env` files, or run anything against
production as the `postgres` superuser except the one-off role script in Phase 1.

---

## Where things stand

Branch `add-mcp-server` (not merged) contains:

| File | What it does |
|---|---|
| `backend/mcp_server.py` | MCP server: 10 tools, 3 resources, stdio + HTTP modes |
| `backend/MCP_SETUP.md` | Setup reference (local, hosted, connector) |
| `create_readonly_role.sql` | SELECT-only `playintel_reader` role for Supabase |
| `backend/main.py` | `get_db_connection()` now read-only with a 15s timeout |
| `backend/requirements.txt` | adds `mcp>=2.3` |

Already verified, in a scratch Postgres built from this repo's own SQL with synthetic games:
all 10 tools over stdio and HTTP; bearer-token auth (401 without key); write attempts
rejected; `users` table and `pg_terminate_backend` blocked for `playintel_reader`.
**Not yet verified: anything against the real Supabase data.**

### Repo notes for Claude Code
- `backend/main.py` – FastAPI; `/api/chat` turns questions into SQL with Claude
- `etl/daily_refresh.py` – daily GitHub Action that rebuilds `fact_game_metrics` and aggregates (uses the superuser `DATABASE_URL` secret; leave it alone)
- `landing/` – Next.js site with auth and Stripe (Vercel); `frontend/` – older React app
- Prefer `agg_*` tables for market questions. Tags are Title Case with hyphens (`Rogue-like`, `Farming Sim`). `total_owners` is a SteamSpy estimate, not sales.
- The MCP SDK is **v2** (`from mcp.server.mcpserver import MCPServer`). Older tutorials use `FastMCP`; don't "fix" the import back.
- `populate_aggregate_tables.py` `main()` has a hard-coded macOS path; call its `populate_*` functions directly if needed.

---

## Phase 0 – Get the branch

```bash
git fetch origin && git checkout add-mcp-server
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
```

Check: `python -c "import sys; sys.path.insert(0,'backend'); import mcp_server"` with any `DATABASE_URL` set imports without error.

## Phase 1 – Read-only database role

1. **[YOU]** Open `create_readonly_role.sql`, replace `CHANGE_ME_long_random_password` with a long random password (keep it out of git), and run the script in the Supabase SQL editor.
2. **[YOU]** If any analytics table has Row Level Security on (the script shows the query to check), add the `reader_all` policy it describes.
3. **[YOU]** Put the reader connection string in your shell, not in a file:
   ```bash
   export PLAYINTEL_DATABASE_URL="postgresql://playintel_reader.<project-ref>:<password>@aws-1-eu-west-1.pooler.supabase.com:5432/postgres"
   ```
4. Claude Code checks the role from the shell:
   ```bash
   psql "$PLAYINTEL_DATABASE_URL" -c "select count(*) from agg_tag_stats"        # > 0
   psql "$PLAYINTEL_DATABASE_URL" -c "select count(*) from users"                # permission denied
   psql "$PLAYINTEL_DATABASE_URL" -c "create table t(x int)"                     # read-only error
   ```

Done when: row count > 0 and both of the others fail.

## Phase 2 – Test every tool against real data

Claude Code writes this to a scratch path outside the repo and runs it from `backend/`:

```python
import asyncio, json, os, sys
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

CALLS = [("market_summary",{}),("price_tier_stats",{}),("tag_stats",{"tag":"rogue"}),
 ("genre_stats",{"genre":"rpg"}),("pricing_for_niche",{"tag":"Farming Sim"}),
 ("pricing_for_niche",{"genre":"Action"}),("success_benchmarks",{}),
 ("find_games",{"name":"Hades"}),("developer_benchmark",{"developer":"Supergiant"}),
 ("data_freshness",{}),("run_sql",{"sql":"select count(*) from fact_game_metrics"}),
 ("run_sql",{"sql":"delete from fact_game_metrics"})]

async def main():
    env = dict(os.environ, DATABASE_URL=os.environ["PLAYINTEL_DATABASE_URL"])
    p = StdioServerParameters(command=sys.executable, args=["mcp_server.py"], env=env)
    async with stdio_client(p) as (r, w), ClientSession(r, w) as s:
        await s.initialize()
        for name, args in CALLS:
            out = await s.call_tool(name, args)
            text = out.content[0].text if out.content else ""
            try:
                d = json.loads(text)
                summary = d.get("error") or f"{d.get('row_count', '?')} rows"
            except Exception:
                summary = text[:120]
            print("FAIL" if out.is_error else "ok  ", name, args, "->", summary)

asyncio.run(main())
```

Done when: every analytics call returns rows (not 0), and the `delete` is rejected.
If a tool returns 0 rows, check column/table names in production against
`backend/mcp_server.py` before changing anything; production may differ from the repo SQL.

## Phase 3 – Use it from Claude Code and Claude Desktop

1. Register it for your user only (not committed to the repo):
   ```bash
   claude mcp add --scope local --transport stdio --env DATABASE_URL="$PLAYINTEL_DATABASE_URL" \
     playintel -- "$(pwd)/.venv/bin/python" "$(pwd)/backend/mcp_server.py"
   ```
2. Restart Claude Code, run `/mcp` and confirm `playintel` is connected with 10 tools.
3. **[YOU]** Ask a few real questions and judge the answers:
   - "What should I price a farming sim at?"
   - "How saturated is the roguelike deckbuilder niche, and what's a realistic owner count?"
   - "Compare Supergiant with other developers of similar size."
4. Optional, Claude Desktop: config snippet is in `backend/MCP_SETUP.md` §2.

Done when: answers use the tools (not guesses) and quote sensible numbers.

## Phase 4 – Point the API at the reader role

1. **[YOU]** On the API's host, change `DATABASE_URL` to the reader connection string.
2. Hit `/api/stats` and one `/api/chat` question; both should still work.
3. Keep the superuser URL only in the GitHub Actions secret used by `etl/daily_refresh.py`.

## Phase 5 – Host the MCP server

1. **[YOU]** On the same host as the API, create a second service from this repo, root `backend/`:
   - Start command: `python mcp_server.py`
   - Env: `MCP_TRANSPORT=http`, `DATABASE_URL=<reader url>`, `MCP_API_KEY=<long random string>`
   - Health check path: `/health`
2. Claude Code verifies from the shell:
   ```bash
   curl -s https://<host>/health                                   # {"status":"ok"}
   curl -s -o /dev/null -w "%{http_code}\n" -X POST https://<host>/mcp   # 401
   ```
3. Connect Claude Code to the hosted copy:
   ```bash
   claude mcp add --transport http playintel-hosted https://<host>/mcp \
     --header "Authorization: Bearer $PLAYINTEL_MCP_KEY"
   ```

Done when: `/mcp` shows `playintel-hosted` connected and a tool call works.

## Phase 6 – Merge

1. Open a PR from `add-mcp-server` to `main` (`gh pr create`), summarising Phases 1–5 results.
2. **[YOU]** Review and merge.

## Phase 7 – Public connector (needs a decision first)

Claude.ai and ChatGPT custom connectors sign users in with OAuth, not a shared key.
**[YOU] decide** where sign-in lives: the existing Supabase users or a separate auth
provider. Then Claude Code should:
1. Research the current options for an OAuth 2.1 authorization server that works with
   MCP and with the chosen user store (check current docs; this area moves fast).
2. Wire it into `mcp_server.py` via the SDK's `auth=` / `token_verifier=` options.
3. Map each token to the user's Stripe plan and enforce `PLAN_LIMITS` per user in a
   database table (the current counter in `main.py` is in-memory and resets on deploy).
4. Test end to end by adding the hosted URL as a custom connector in Claude.ai.

---

## Guardrails for Claude Code
- Work on `add-mcp-server` (or a branch off it), never commit straight to `main`.
- No secrets in files, commits, logs or PR text. Use env vars.
- Don't widen `playintel_reader`'s grants or remove the `run_sql` checks to make a query work.
- Don't touch `etl/` or the daily refresh workflow as part of this plan.
