# PlayIntel MCP server

`mcp_server.py` exposes the Steam market dataset to MCP clients (Claude, ChatGPT,
Cursor, Claude Code). The client's model does the reasoning; this server only
serves data, schema and domain knowledge. No Anthropic key is used.

## What it exposes

| Tool | Answers |
|---|---|
| `market_summary` | Overall market numbers |
| `price_tier_stats` | Free vs Budget vs ... vs AAA performance |
| `tag_stats` | Niche saturation and success rate (partial tag match) |
| `genre_stats` | Broad genre comparison |
| `pricing_for_niche` | "What should I price my X game at?" by tag or genre |
| `success_benchmarks` | Ownership and review tiers: what's realistic |
| `find_games` | Individual games / comparables, combinable filters |
| `developer_benchmark` | Developer track record |
| `data_freshness` | When aggregates were last refreshed |
| `run_sql` | Fallback: one read-only SELECT, 200 rows, 15s |

Resources: `playintel://schema`, `playintel://knowledge/analyst`,
`playintel://knowledge/industry`.

## 1. Database role (once)

Run `../create_readonly_role.sql` in the Supabase SQL editor after setting a
password. Use the `playintel_reader` connection string as `DATABASE_URL` for both
the API and the MCP server. Keep the superuser URL for the ETL only.

## 2. Run locally with Claude Desktop / Claude Code

```bash
cd backend && pip install -r requirements.txt
```

Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "playintel": {
      "command": "python",
      "args": ["/absolute/path/to/playintel/backend/mcp_server.py"],
      "env": { "DATABASE_URL": "postgresql://playintel_reader.<ref>:<pw>@...pooler.supabase.com:5432/postgres" }
    }
  }
}
```

Claude Code: `claude mcp add playintel -e DATABASE_URL=... -- python /abs/path/backend/mcp_server.py`

## 3. Host it (second service next to the API)

Create a second service from the same repo (root `backend/`):

- Start command: `python mcp_server.py`
- Env: `MCP_TRANSPORT=http`, `DATABASE_URL=<reader url>`, `MCP_API_KEY=<long random string>`
- Health check: `GET /health`
- MCP endpoint: `https://<host>/mcp`

With `MCP_API_KEY` set, clients must send `Authorization: Bearer <key>`:

```bash
claude mcp add --transport http playintel https://<host>/mcp \
  --header "Authorization: Bearer <key>"
```

## 4. Public connector (next phase)

Claude.ai and ChatGPT custom connectors sign users in with OAuth rather than a
static key. To list PlayIntel as a connector for paying users, add an OAuth
provider and map each token to the user's Stripe plan so `PLAN_LIMITS` apply.

## Testing

`create_aggregate_tables.sql` + `populate_aggregate_tables.py` against a scratch
database is enough to exercise every tool; all tools were verified that way.
