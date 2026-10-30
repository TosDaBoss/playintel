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

## 3. Host it with an API key (Claude Code, Cursor, testing)

Run with `MCP_TRANSPORT=http`, `DATABASE_URL=<reader url>` and
`MCP_API_KEY=<long random string>`. Clients send `Authorization: Bearer <key>`:

```bash
claude mcp add --transport http playintel https://<host>/mcp \
  --header "Authorization: Bearer <key>"
```

HTTP mode refuses to start unless `MCP_API_KEY` or OAuth (section 4) is set.

## 4. Public connector: Cloud Run + WorkOS sign-up (pattern from Grove)

Claude.ai and ChatGPT connectors sign users in with OAuth. The server is an OAuth
resource server (`mcp_auth.py`): WorkOS AuthKit signs people up and in and issues
JWTs; the server verifies them. Sign-up is open, so anyone who signs up gets
access. WorkOS keeps every user's email (Users page, exportable), and the server
logs `MCP user: <email>` the first time each user calls it on an instance.

The link to share is the server root, `https://<host>/`: a page with a sign-up
button, the connector URL and how to add it in Claude and ChatGPT.

### WorkOS (once, in a WorkOS account for PlayIntel only)

Use a separate account or environment from Grove: Grove keeps sign-up closed,
PlayIntel needs it open. Menu names move; check WorkOS's current MCP docs.

1. Authentication: turn on email sign-up (password or magic link; Google optional) and leave sign-ups open.
2. Turn on dynamic client registration (the MCP / OAuth applications setting) so Claude and ChatGPT can register themselves.
3. JWT template: `{"email": {{ user.email }}}` (no quotes around the placeholder). Without it every user is refused.
4. Redirects: set the default redirect / sign-in URI to `https://<host>/`, so people who use the sign-up button land back on the page.
5. Note the AuthKit domain (`https://<name>.authkit.app`) and the environment's client ID (`client_...`).

### Deploy

```bash
gcloud auth login
source ~/.playintel_env     # PLAYINTEL_DATABASE_URL = the playintel_reader URL
PROJECT_ID=<gcp project> AUTHKIT_DOMAIN=https://<name>.authkit.app WORKOS_CLIENT_ID=client_... \
  deploy/mcp_cloud_run.sh
```

The script stores the reader URL in Secret Manager, deploys `backend/` with its
`Dockerfile`, and prints the page and connector URLs. `backend/.env` is excluded
from the upload by `.gcloudignore`.

### Pitfalls (from Grove)

| Symptom | Fix |
|---|---|
| Every sign-in refused: "Audience doesn't match" | `OAUTH_AUDIENCE` must be the WorkOS client ID; the log line shows the token's `aud` |
| Sign-in works but "user refused" in the logs | JWT template missing, so the token has no `email` |
| ChatGPT 403 | `MCP_ALLOWED_ORIGINS` must include chatgpt.com (it does by default) |
| `/healthz` 404 on Cloud Run | Use `/health` |
| New deploy serves 0% of traffic | `update-traffic --to-latest` (the script does it) |
| ChatGPT shows old tools | Disconnect and reconnect the connector |

Logs: `gcloud run services logs read playintel-mcp --region europe-west2 --limit 40`

To close access again, set `ALLOWED_EMAILS` or `ALLOWED_EMAIL_DOMAIN` on the
service. Payments and per-user plan limits are not wired in yet.

## Testing

`create_aggregate_tables.sql` + `populate_aggregate_tables.py` against a scratch
database is enough to exercise every tool; all tools were verified that way.
