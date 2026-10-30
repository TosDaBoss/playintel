"""
PlayIntel MCP server
Exposes the Steam market dataset to any MCP client (Claude, ChatGPT, Cursor...).

The client's own model does the reasoning, so this server does no Anthropic
calls: it just serves data, schema and domain knowledge.

Run locally (stdio):   python mcp_server.py
Run remotely (HTTP):   MCP_TRANSPORT=http PORT=8001 python mcp_server.py
Hosted with sign-in:   see MCP_SETUP.md section 4 (WorkOS + Cloud Run)
"""

import html
import logging
import os
import re
from decimal import Decimal
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal, Optional

import psycopg
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

load_dotenv()
# main.py builds an Anthropic client at import; the MCP server never calls it
os.environ.setdefault("ANTHROPIC_API_KEY", "unused-by-mcp")
# Reuse the schema text the chat endpoint already gives Claude
from main import get_database_schema  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL")
HERE = Path(__file__).parent
MAX_ROWS = 200

# OAuth (WorkOS AuthKit) for the public connector; unset for local stdio use
OAUTH_ISSUER_URL = os.getenv("OAUTH_ISSUER_URL")
MCP_PUBLIC_URL = os.getenv("MCP_PUBLIC_URL")
auth_kwargs: dict[str, Any] = {}
if OAUTH_ISSUER_URL:
    from mcp.server.auth.settings import AuthSettings
    from mcp_auth import JwtVerifier

    if not MCP_PUBLIC_URL:
        raise ValueError("MCP_PUBLIC_URL is required when OAuth is enabled")
    auth_kwargs["token_verifier"] = JwtVerifier.from_env()
    # WorkOS puts its client ID in `aud`, not this URL, so JwtVerifier checks the audience itself
    auth_kwargs["auth"] = AuthSettings(issuer_url=OAUTH_ISSUER_URL, resource_server_url=MCP_PUBLIC_URL,
                                       validate_token_resource=False)

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False,
                            idempotent_hint=True, open_world_hint=False)

mcp = MCPServer(
    "playintel",
    title="PlayIntel: Steam market intelligence",
    **auth_kwargs,
    instructions=(
        "Steam market intelligence for indie game developers (~77k games). "
        "Prefer the specific tools (price tiers, tags, genres, tag pricing, game lookup, "
        "developer benchmarks) and use run_sql only for questions they cannot answer. "
        "Read the playintel://schema resource before writing SQL. Tags are Title Case "
        "with hyphens (e.g. 'Rogue-like', 'Farming Sim'); match with ILIKE when unsure. "
        "Owner counts are SteamSpy estimates, not sales: say so when quoting them. "
        "Call data_freshness if the user asks how current the data is."
    ),
)


# ---------- helpers ----------

def _jsonable(v: Any) -> Any:
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    return v


def _query(sql: str, params: tuple = (), limit: int = MAX_ROWS) -> dict:
    """Run a query in a READ ONLY transaction with a timeout."""
    with psycopg.connect(DATABASE_URL) as conn:
        conn.read_only = True
        with conn.cursor() as cur:
            cur.execute("SET LOCAL statement_timeout = '15s'")
            cur.execute(sql, params)
            cols = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(limit + 1)
    truncated = len(rows) > limit
    return {
        "columns": cols,
        "rows": [{c: _jsonable(v) for c, v in zip(cols, r)} for r in rows[:limit]],
        "row_count": min(len(rows), limit),
        "truncated": truncated,
    }


# ---------- resources (context the model can read) ----------

@mcp.resource("playintel://schema")
def schema() -> str:
    """Database schema, table purposes and tag-naming rules."""
    return get_database_schema()


@mcp.resource("playintel://knowledge/analyst")
def analyst_knowledge() -> str:
    """How to interpret Steam metrics (the 'Alex' analyst knowledge base)."""
    return (HERE / "alex_knowledge_base.txt").read_text()


@mcp.resource("playintel://knowledge/industry")
def industry_knowledge() -> str:
    """Indie game industry background knowledge."""
    return (HERE / "indie_game_industry_knowledge.txt").read_text()


# ---------- tools ----------

@mcp.tool(annotations=READ_ONLY)
def market_summary() -> dict:
    """Overall Steam market stats: game counts, owners, average price, playtime, rating."""
    return _query("SELECT * FROM summary_stats LIMIT 1")


@mcp.tool(annotations=READ_ONLY)
def price_tier_stats() -> dict:
    """Performance by price tier (Free through AAA $50+): owners, rating, playtime,
    hours per dollar and share of games reaching 100k owners."""
    return _query("SELECT * FROM agg_price_tier_stats ORDER BY sort_order")


@mcp.tool(annotations=READ_ONLY)
def tag_stats(tag: Optional[str] = None, sort_by: Literal[
        "game_count", "avg_owners", "median_owners", "avg_rating", "success_rate_100k"
    ] = "game_count", limit: int = 25) -> dict:
    """Niche/tag market analysis (saturation, typical owners, success rate).
    Pass `tag` as a partial name (e.g. 'rogue', 'farm') or omit it to rank all tags."""
    if tag:
        return _query(
            f"SELECT * FROM agg_tag_stats WHERE tag ILIKE %s ORDER BY {sort_by} DESC LIMIT %s",
            (f"%{tag}%", limit),
        )
    return _query(f"SELECT * FROM agg_tag_stats ORDER BY {sort_by} DESC LIMIT %s", (limit,))


@mcp.tool(annotations=READ_ONLY)
def genre_stats(genre: Optional[str] = None) -> dict:
    """Broad genre market analysis. Pass a partial genre name or omit for all 28 genres."""
    if genre:
        return _query("SELECT * FROM agg_genre_stats WHERE genre ILIKE %s", (f"%{genre}%",))
    return _query("SELECT * FROM agg_genre_stats ORDER BY game_count DESC")


@mcp.tool(annotations=READ_ONLY)
def pricing_for_niche(tag: Optional[str] = None, genre: Optional[str] = None) -> dict:
    """'What should I price my X game at?' Returns per-price-tier performance for a tag
    (agg_tag_price_matrix) or a genre (agg_genre_price_performance). Give one of them."""
    if tag:
        return _query(
            """SELECT m.* FROM agg_tag_price_matrix m
               JOIN agg_price_tier_stats p USING (price_category)
               WHERE m.tag ILIKE %s ORDER BY m.tag, p.sort_order""",
            (f"%{tag}%",),
        )
    if genre:
        return _query(
            """SELECT g.* FROM agg_genre_price_performance g
               JOIN agg_price_tier_stats p USING (price_category)
               WHERE g.genre ILIKE %s ORDER BY g.genre, p.sort_order""",
            (f"%{genre}%",),
        )
    return {"error": "Pass either tag or genre."}


@mcp.tool(annotations=READ_ONLY)
def success_benchmarks() -> dict:
    """What's realistic? Ownership tiers (Small <10K up to Mega 10M+) with the share of
    games in each, plus review-tier stats."""
    return {
        "ownership_tiers": _query("SELECT * FROM agg_ownership_tier_stats ORDER BY sort_order"),
        "review_tiers": _query("SELECT * FROM agg_review_tier_stats ORDER BY sort_order"),
    }


@mcp.tool(annotations=READ_ONLY)
def find_games(name: Optional[str] = None, tag: Optional[str] = None,
               developer: Optional[str] = None, price_category: Optional[str] = None,
               min_owners: Optional[int] = None, sort_by: Literal[
                   "total_owners", "rating_percentage", "total_reviews", "ccu", "price_usd"
               ] = "total_owners", limit: int = 20) -> dict:
    """Look up individual games or comparables. All filters are optional and combine."""
    where, params = [], []
    if name:
        where.append("name ILIKE %s"); params.append(f"%{name}%")
    if tag:
        where.append("top_tags ILIKE %s"); params.append(f"%{tag}%")
    if developer:
        where.append("developer ILIKE %s"); params.append(f"%{developer}%")
    if price_category:
        where.append("price_category ILIKE %s"); params.append(f"%{price_category}%")
    if min_owners is not None:
        where.append("total_owners >= %s"); params.append(min_owners)
    sql = f"""SELECT appid, name, developer, publisher, price_usd, price_category,
                     total_owners, rating_percentage, review_category, total_reviews,
                     avg_hours_played, ccu, genres, top_tags
              FROM fact_game_metrics
              {'WHERE ' + ' AND '.join(where) if where else ''}
              ORDER BY {sort_by} DESC NULLS LAST LIMIT %s"""
    params.append(min(limit, MAX_ROWS))
    return _query(sql, tuple(params))


@mcp.tool(annotations=READ_ONLY)
def developer_benchmark(developer: str) -> dict:
    """Benchmark a developer (3+ games): totals, average owners per game, best game."""
    return _query(
        """SELECT * FROM agg_developer_stats WHERE developer ILIKE %s
           ORDER BY (developer ILIKE %s) DESC, total_owners DESC LIMIT 20""",
        (f"%{developer}%", developer),
    )


@mcp.tool(annotations=READ_ONLY)
def data_freshness() -> dict:
    """When each aggregate table was last refreshed."""
    return _query("SELECT * FROM agg_refresh_log ORDER BY last_refreshed DESC")


_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|do|vacuum)\b",
    re.I,
)


@mcp.tool(annotations=READ_ONLY)
def run_sql(sql: str) -> dict:
    """Escape hatch: run a single read-only SELECT against the PlayIntel database.
    Read the playintel://schema resource first. Max 200 rows, 15s timeout."""
    stripped = sql.strip().rstrip(";")
    if ";" in stripped or not re.match(r"^\s*(select|with)\b", stripped, re.I) \
            or _FORBIDDEN.search(stripped):
        return {"error": "Only a single SELECT/WITH statement is allowed."}
    try:
        return _query(stripped)
    except psycopg.Error as e:
        # Hand the message back so the model can correct its SQL and retry
        return {"error": str(e).strip().splitlines()[0], "hint": "Check playintel://schema"}


# ---------- HTTP hosting ----------

SIGNUP_URL = os.getenv("SIGNUP_URL") or (f"{OAUTH_ISSUER_URL}/sign-up" if OAUTH_ISSUER_URL else "")


@mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
async def health(request):
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok"})


@mcp.custom_route("/", methods=["GET"], include_in_schema=False)
async def connect_page(request):
    """The link to share: what PlayIntel is, sign-up, and how to add the connector.
    WorkOS redirects here after a direct sign-up (with ?code=...), so show a welcome."""
    from starlette.responses import HTMLResponse

    connector_url = MCP_PUBLIC_URL or str(request.base_url).rstrip("/") + "/mcp"
    signed_up = "code" in request.query_params or "signed_up" in request.query_params
    page = (HERE / "mcp_connect.html").read_text()
    for key, value in {
        "CONNECTOR_URL": connector_url,
        "SIGNUP_URL": SIGNUP_URL or "#",
        "WELCOME_HIDDEN": "" if signed_up else "hidden",
        "SIGNUP_HIDDEN": "hidden" if signed_up or not SIGNUP_URL else "",
    }.items():
        page = page.replace("{{" + key + "}}", html.escape(value))
    return HTMLResponse(page)


def _transport_security():
    """Same rule as Grove: once the public host is known, only accept that Host
    header and browser origins from the AI clients (Claude, ChatGPT)."""
    from mcp.server.transport_security import TransportSecuritySettings

    hosts = [h.strip() for h in (os.getenv("MCP_ALLOWED_HOSTS") or "").split(",") if h.strip()]
    if not hosts:
        return None
    origins = os.getenv("MCP_ALLOWED_ORIGINS",
                        "https://claude.ai,https://chatgpt.com,https://chat.openai.com")
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=[f"https://{h}" for h in hosts] + [o.strip() for o in origins.split(",") if o.strip()],
    )


def http_app():
    """ASGI app for hosting (Cloud Run). Stateless so it can scale out.

    With OAUTH_ISSUER_URL set, /mcp requires a WorkOS access token (claude.ai and
    ChatGPT connectors). Otherwise MCP_API_KEY must be set and every /mcp request
    must send `Authorization: Bearer <MCP_API_KEY>` (Claude Code, Cursor, testing).
    """
    import hmac
    from starlette.responses import JSONResponse

    api_key = os.getenv("MCP_API_KEY")
    if not OAUTH_ISSUER_URL and not api_key:
        raise SystemExit("Refusing to serve HTTP without sign-in: set OAUTH_ISSUER_URL or MCP_API_KEY")
    app = mcp.streamable_http_app(stateless_http=True, json_response=True, host="0.0.0.0",
                                  transport_security=_transport_security())
    if OAUTH_ISSUER_URL:
        return app

    async def guarded(scope, receive, send):
        if scope["type"] == "http" and scope["path"].startswith("/mcp"):
            auth = dict(scope.get("headers") or []).get(b"authorization", b"").decode()
            if not hmac.compare_digest(auth, f"Bearer {api_key}"):
                return await JSONResponse({"error": "unauthorized"}, status_code=401)(
                    scope, receive, send)
        await app(scope, receive, send)

    return guarded


if __name__ == "__main__":
    if os.getenv("MCP_TRANSPORT", "stdio") == "http":
        import uvicorn

        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
        uvicorn.run(http_app(), host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
    else:
        mcp.run()
