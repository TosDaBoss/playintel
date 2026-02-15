"""
PlayIntel - AI-Powered Steam Market Intelligence
FastAPI Backend with Claude AI Integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import psycopg
from anthropic import Anthropic
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="PlayIntel API",
    description="AI-powered Steam market intelligence for indie game developers",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Claude AI
anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    """Create a database connection."""
    return psycopg.connect(DATABASE_URL)


def get_interpretation_prompt(question: str, data: list, data_count: int) -> str:
    """Generate the interpretation prompt for Claude with improved variety and rules."""

    # Check if user is asking for a chart/visualization
    question_lower = question.lower()
    chart_keywords = ['chart', 'graph', 'plot', 'visualize', 'visualization', 'show me a chart', 'bar chart', 'pie chart']
    user_wants_chart = any(kw in question_lower for kw in chart_keywords)

    chart_instruction = ""
    if user_wants_chart:
        chart_instruction = """
CHART REQUEST DETECTED:
The system automatically generates charts from this data. A visualization will appear alongside your text response.
DO NOT say "I cannot generate charts" or "I don't have chart capability" - the chart IS being generated.
Simply provide your text analysis of the data. The chart will be displayed automatically."""

    return f"""Answer this Steam market question directly.

Question: "{question}"

Data:
{json.dumps(data[:50], indent=2)}
{"(Showing first 50 of " + str(data_count) + " results)" if data_count > 50 else ""}
{chart_instruction}

CRITICAL RULES:
1. START WITH THE ANSWER - No preamble, no "Great question!", no self-introduction
2. NEVER introduce yourself - No "I'm an analyst", "As an expert", "With X years experience"
3. NEVER mention: SQL, queries, databases, tables, dataset, "looking at the data", "let me check"
4. NEVER use filler phrases: "Certainly!", "Absolutely!", "I'd be happy to", "Great question"
5. Use "you/your" when addressing the user directly
6. If data is missing, pivot smoothly: "Review counts suggest..." not "I don't have that data"
7. NEVER say you cannot generate charts/graphs - the system handles visualization automatically

RESPONSE PATTERNS - Match to question type:

Quick Answer (counts, averages, single values):
Start with the number. Add one line of context max.
"4.6 hours average - typical for this price tier."
"327 games total."

List (top X, show me):
Lead with the list, no intro needed.
"1. Counter-Strike - 150M owners, 86% rating
2. PUBG - 150M owners, 75% rating
3. Apex Legends - 150M owners, 72% rating"

Comparison:
State the key difference first.
"Roguelikes average 15% higher ratings than city builders at this price point."

Recommendation:
Give the recommendation, then the reasoning.
"Price at £15. Games in that range see 2x the conversion of £20 titles."

RESPONSE LENGTH:
- Simple questions: 20-60 words
- Complex analysis: 80-150 words
- Never pad with unnecessary advice

TONE:
Direct, knowledgeable, conversational. Like a Slack message from a colleague who knows the market well."""


def get_database_schema():
    """Get the database schema for Claude AI context."""
    return """
    Database Schema for Steam Market Intelligence:

    === PRIMARY DATA TABLE ===

    1. fact_game_metrics (77,274 games)
       HIGH COVERAGE (90%+):
       - appid (PRIMARY KEY)
       - name, developer, publisher
       - price_category (TEXT: 'Free', 'Budget ($0-$5)', 'Low ($5-$10)', 'Medium ($10-$20)', 'Standard ($20-$30)', 'Premium ($30-$50)', 'AAA ($50+)')
       - total_owners (estimated ownership from SteamSpy)
       - positive_reviews, total_reviews, rating_percentage
       - review_category (Overwhelmingly Positive, Very Positive, Mostly Positive, Mixed, Mostly Negative, Negative, Overwhelmingly Negative, Insufficient Reviews)
       - genres, top_tags (comma-separated lists)
       - created_at, updated_at

       MEDIUM COVERAGE (20-90%):
       - price_usd (87%), initialprice_usd
       - avg_hours_played (27%), median_hours_played
       - ccu (21% - peak concurrent users)
       - hours_per_dollar (23%)
       - negative_reviews (80%)
       - engagement_score (27%)

    === PRE-COMPUTED AGGREGATE TABLES (USE THESE FOR FAST QUERIES!) ===

    2. agg_price_tier_stats (7 rows - one per price tier)
       - price_category (PRIMARY KEY), sort_order
       - game_count, avg_owners, median_owners
       - avg_rating, avg_playtime_hours, avg_hours_per_dollar
       - games_90plus_rating, games_1m_plus_owners, success_rate_100k
       USE FOR: Price tier comparisons, pricing strategy questions

    3. agg_tag_stats (440 tags with 10+ games each)
       - tag (PRIMARY KEY)
       - game_count, avg_owners, median_owners
       - avg_rating, avg_price
       - games_90plus_rating, games_1m_plus_owners, success_rate_100k
       USE FOR: Tag/niche market analysis, "how saturated is X tag?"

    4. agg_genre_stats (28 genres with 10+ games each)
       - genre (PRIMARY KEY)
       - game_count, avg_owners, median_owners
       - avg_rating, avg_price
       - games_90plus_rating, games_1m_plus_owners, success_rate_100k
       USE FOR: Genre market analysis, "how competitive is X genre?"

    5. agg_ownership_tier_stats (5 tiers)
       - ownership_tier (PRIMARY KEY): 'Mega (10M+)', 'Hit (1M-10M)', 'Success (100K-1M)', 'Moderate (10K-100K)', 'Small (<10K)'
       - sort_order, min_owners, max_owners
       - game_count, avg_rating, avg_price, avg_playtime, pct_of_total
       USE FOR: Success benchmarking, "what's realistic for my game?"

    6. agg_review_tier_stats (7 review categories)
       - review_category (PRIMARY KEY), sort_order
       - min_rating, max_rating, game_count
       - avg_owners, avg_reviews, avg_price
       USE FOR: Review threshold questions, rating expectations

    7. agg_tag_price_matrix (2,436 tag+price combinations)
       - tag, price_category (COMPOSITE PRIMARY KEY)
       - game_count, avg_owners, avg_rating, success_rate_100k
       USE FOR: "What should I price my roguelike at?" - specific pricing by niche

    8. agg_genre_price_performance (169 genre+price combinations)
       - genre, price_category (COMPOSITE PRIMARY KEY)
       - game_count, avg_owners, avg_rating, success_rate_100k
       USE FOR: Genre-specific pricing recommendations

    9. agg_developer_stats (4,457 developers with 3+ games)
       - developer (PRIMARY KEY)
       - game_count, total_owners, avg_owners_per_game, avg_rating
       - best_game_name, best_game_owners, primary_genres
       USE FOR: Developer benchmarking, competitor analysis

    10. agg_refresh_log (tracks when aggregate tables were last updated)
        - table_name (PRIMARY KEY), last_refreshed, row_count, refresh_duration_seconds

    === LEGACY DIMENSION TABLES ===

    11. dim_developers (49,768 developers)
        - developer_id, developer, total_games, paid_games, free_games
        - total_owners, avg_owners_per_game, total_reviews, overall_rating_percentage

    12. dim_publishers (44,125 publishers)
        - Same structure as dim_developers

    13. summary_stats (1 row - overall market stats)
        - total_games, free_games, paid_games
        - total_owners, avg_playtime_hours, avg_price_paid_games
        - avg_rating, total_reviews_submitted
        - unique_developers, unique_publishers

    === QUERY STRATEGY ===

    PREFER aggregate tables for common questions:
    - "What's the average for X price tier?" → agg_price_tier_stats
    - "How many roguelike games?" → agg_tag_stats WHERE tag ILIKE '%rogue%'
    - "Best price for action games?" → agg_genre_price_performance WHERE genre ILIKE '%action%'
    - "What rating do successful games have?" → agg_ownership_tier_stats
    - "Compare review categories" → agg_review_tier_stats

    Use fact_game_metrics for:
    - Specific game lookups by name
    - Custom filtering not in aggregate tables
    - Getting individual game details

    CRITICAL - ALWAYS USE CASE-INSENSITIVE QUERIES:
    - Tags are stored with Title Case and hyphens (e.g., "Rogue-like", "Roguelike Deckbuilder", "Farming Sim")
    - ALWAYS use ILIKE for tag/genre matching: WHERE tag ILIKE '%roguelike%' or WHERE tag ILIKE '%rogue%'
    - NEVER use exact case-sensitive matches like WHERE tag = 'roguelike' (will return 0 results!)
    - For multiple terms, use: WHERE tag ILIKE '%rogue%' AND tag ILIKE '%deck%'

    COMMON TAG MAPPINGS (use ILIKE with these patterns):
    - Roguelike/Roguelite → '%rogue%' (matches: Rogue-like, Rogue-lite, Action Roguelike, Roguelike Deckbuilder)
    - Farming/Farming Sim → '%farm%' (matches: Farming, Farming Sim)
    - Horror → '%horror%' (matches: Horror, Survival Horror, Psychological Horror)
    - Deckbuilder → '%deck%' or '%deckbuilder%' (matches: Roguelike Deckbuilder, Deckbuilding)

    MULTI-GENRE/TAG COMPARISON QUERIES:
    When comparing multiple genres/tags, use UNION ALL to get data for each.
    IMPORTANT: Use agg_tag_stats for specific niches (roguelike, farming sim) and agg_genre_stats for broad genres.

    VERIFIED EXACT TAG NAMES IN DATABASE (ALWAYS use these exact values):
    - 'Roguelike Deckbuilder' (324 games) - MUST use: tag = 'Roguelike Deckbuilder'
    - 'Farming Sim' (624 games) - MUST use: tag = 'Farming Sim'
    - 'Horror' (6487 games) - MUST use: tag = 'Horror'
    - 'Survival Horror' (1972 games) - MUST use: tag = 'Survival Horror'
    - 'Psychological Horror' (3604 games) - MUST use: tag = 'Psychological Horror'
    - 'Rogue-like' (3267 games) - MUST use: tag = 'Rogue-like'
    - 'Rogue-lite' (3272 games) - MUST use: tag = 'Rogue-lite'
    - 'Action Roguelike' (2758 games) - MUST use: tag = 'Action Roguelike'
    - 'Deckbuilding' (819 games) - MUST use: tag = 'Deckbuilding'
    - 'Farming' (97 games) - Note: smaller than 'Farming Sim'

    Example: "Compare roguelike deckbuilder, farming sim, and horror games"
    SELECT 'Roguelike Deckbuilder' as category, game_count, avg_rating, avg_owners, success_rate_100k
    FROM agg_tag_stats WHERE tag = 'Roguelike Deckbuilder'
    UNION ALL
    SELECT 'Farming Sim' as category, game_count, avg_rating, avg_owners, success_rate_100k
    FROM agg_tag_stats WHERE tag = 'Farming Sim'
    UNION ALL
    SELECT 'Horror' as category, game_count, avg_rating, avg_owners, success_rate_100k
    FROM agg_tag_stats WHERE tag = 'Horror'

    CRITICAL: Use exact tag names with = operator, NOT ILIKE patterns!
    """


# Plan tier configurations
PLAN_LIMITS = {
    'free': 30,
    'indie': 150,
    'studio': -1,  # unlimited
}

# In-memory query tracking (in production, use Redis or database)
# Format: { user_id: { 'count': int, 'reset_date': str } }
query_usage_tracker: Dict[str, Dict[str, Any]] = {}


def get_next_reset_date() -> str:
    """Get the first of next month as ISO string."""
    from datetime import datetime
    now = datetime.now()
    if now.month == 12:
        next_month = datetime(now.year + 1, 1, 1)
    else:
        next_month = datetime(now.year, now.month + 1, 1)
    return next_month.isoformat()


def check_query_limit(user_id: str, plan: str) -> Dict[str, Any]:
    """Check if user can make a query based on their plan."""
    from datetime import datetime

    limit = PLAN_LIMITS.get(plan, 5)

    # Unlimited plan
    if limit == -1:
        return {'allowed': True, 'remaining': -1, 'limit': -1, 'used': 0, 'reset_date': get_next_reset_date()}

    # Get or initialize user's usage
    if user_id not in query_usage_tracker:
        query_usage_tracker[user_id] = {
            'count': 0,
            'reset_date': get_next_reset_date()
        }

    usage = query_usage_tracker[user_id]

    # Check if we need to reset (new month)
    if datetime.now() >= datetime.fromisoformat(usage['reset_date']):
        usage['count'] = 0
        usage['reset_date'] = get_next_reset_date()

    remaining = limit - usage['count']

    return {
        'allowed': remaining > 0,
        'remaining': max(0, remaining),
        'limit': limit,
        'used': usage['count'],
        'reset_date': usage['reset_date']
    }


def increment_query_count(user_id: str):
    """Increment the query count for a user."""
    from datetime import datetime

    if user_id not in query_usage_tracker:
        query_usage_tracker[user_id] = {
            'count': 0,
            'reset_date': get_next_reset_date()
        }

    usage = query_usage_tracker[user_id]

    # Check if we need to reset first
    if datetime.now() >= datetime.fromisoformat(usage['reset_date']):
        usage['count'] = 1
        usage['reset_date'] = get_next_reset_date()
    else:
        usage['count'] += 1


def analyze_data_for_visualization(data: List[Dict], question: str) -> Optional[Dict[str, Any]]:
    """
    Analyze data to determine if visualization would be beneficial and what type.
    Uses data analytics principles to select the best chart type.

    Returns chart_config if visualization is appropriate, None otherwise.
    """
    if not data or len(data) < 2:
        return None

    # Get the columns/keys from the data
    columns = list(data[0].keys())
    num_rows = len(data)

    # Identify column types
    numeric_cols = []
    categorical_cols = []

    for col in columns:
        sample_values = [row.get(col) for row in data[:10] if row.get(col) is not None]
        if sample_values:
            if all(isinstance(v, (int, float)) for v in sample_values):
                numeric_cols.append(col)
            else:
                categorical_cols.append(col)

    # Decision logic based on data analytics principles
    question_lower = question.lower()

    # Check for explicit chart requests
    wants_chart = any(word in question_lower for word in ['chart', 'graph', 'plot', 'visualize', 'visualization', 'show me a'])

    # Special case: categorical distribution (e.g., count by category/tier)
    # If we have categorical data without numeric values, we can count occurrences
    if len(categorical_cols) >= 2 and len(numeric_cols) == 0:
        # Check if this is a distribution/breakdown type query
        distribution_keywords = ['tier', 'category', 'type', 'breakdown', 'distribution', 'pricing', 'price']
        is_categorical_distribution = any(kw in question_lower for kw in distribution_keywords)

        if is_categorical_distribution or wants_chart:
            # Find the category column (tier, category, type, etc.)
            category_col = None
            label_col = None
            for col in categorical_cols:
                col_lower = col.lower()
                if any(cat in col_lower for cat in ['tier', 'category', 'type', 'price', 'rating', 'genre']):
                    category_col = col
                elif any(name in col_lower for name in ['name', 'title', 'game', 'developer']):
                    label_col = col

            if category_col and label_col:
                # Create aggregated data by counting occurrences per category
                category_counts = {}
                for row in data:
                    cat = row.get(category_col, 'Unknown')
                    if cat not in category_counts:
                        category_counts[cat] = 0
                    category_counts[cat] += 1

                # Convert to chart data format
                aggregated_data = [
                    {category_col: cat, 'count': count}
                    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1])
                ]

                if len(aggregated_data) <= 8:
                    return {
                        "type": "donut",
                        "data": aggregated_data,
                        "config": {
                            "nameKey": category_col,
                            "valueKey": "count",
                            "title": None
                        }
                    }
                else:
                    return {
                        "type": "horizontal_bar",
                        "data": aggregated_data,
                        "config": {
                            "labelKey": category_col,
                            "valueKey": "count",
                            "secondaryKey": None,
                            "percentKey": None,
                            "title": None
                        }
                    }

    # If user explicitly wants a chart, or data is suitable for visualization
    if wants_chart or (num_rows >= 3 and num_rows <= 20 and len(numeric_cols) >= 1):

        # Determine best chart type based on data characteristics

        # 1. HORIZONTAL BAR: Best for comparing categories with values (rankings, comparisons)
        # Good for: top X lists, category comparisons, showing distributions
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            # Check if this looks like a ranking/comparison query
            ranking_keywords = ['top', 'best', 'worst', 'highest', 'lowest', 'most', 'least',
                              'compare', 'ranking', 'by', 'per', 'breakdown']
            is_ranking = any(kw in question_lower for kw in ranking_keywords)

            if is_ranking or num_rows <= 15:
                # Find the best label column (prefer name-like columns)
                label_col = None
                for col in categorical_cols:
                    if any(name in col.lower() for name in ['name', 'title', 'developer', 'publisher', 'genre', 'tag', 'category', 'tier']):
                        label_col = col
                        break
                if not label_col:
                    label_col = categorical_cols[0]

                # Find the primary value column
                value_col = numeric_cols[0]
                for col in numeric_cols:
                    if any(val in col.lower() for val in ['owner', 'count', 'total', 'revenue', 'sales', 'rating', 'score']):
                        value_col = col
                        break

                # Find secondary/percent columns if available
                secondary_col = None
                percent_col = None
                for col in numeric_cols:
                    if col != value_col:
                        if 'percent' in col.lower() or 'rate' in col.lower() or 'ratio' in col.lower():
                            percent_col = col
                        elif secondary_col is None:
                            secondary_col = col

                return {
                    "type": "horizontal_bar",
                    "data": data,
                    "config": {
                        "labelKey": label_col,
                        "valueKey": value_col,
                        "secondaryKey": secondary_col,
                        "percentKey": percent_col,
                        "title": None  # Let the answer provide context
                    }
                }

        # 2. PIE/DONUT: Best for showing parts of a whole (distributions, market share)
        # Good for: percentage breakdowns, market share, composition
        distribution_keywords = ['distribution', 'breakdown', 'share', 'proportion', 'percentage', 'split', 'composition']
        is_distribution = any(kw in question_lower for kw in distribution_keywords)

        if is_distribution and len(categorical_cols) >= 1 and len(numeric_cols) >= 1 and num_rows <= 8:
            name_col = categorical_cols[0]
            value_col = numeric_cols[0]

            return {
                "type": "donut",
                "data": data,
                "config": {
                    "nameKey": name_col,
                    "valueKey": value_col,
                    "title": None
                }
            }

        # 3. SCATTER: Best for showing relationships between two numeric variables
        # Good for: correlation, patterns, outliers
        correlation_keywords = ['correlation', 'relationship', 'vs', 'versus', 'against', 'compared to']
        is_correlation = any(kw in question_lower for kw in correlation_keywords)

        if is_correlation and len(numeric_cols) >= 2:
            x_col = numeric_cols[0]
            y_col = numeric_cols[1]
            name_col = categorical_cols[0] if categorical_cols else None

            return {
                "type": "scatter",
                "data": data,
                "config": {
                    "xKey": x_col,
                    "yKey": y_col,
                    "nameKey": name_col,
                    "xLabel": x_col.replace('_', ' ').title(),
                    "yLabel": y_col.replace('_', ' ').title(),
                    "title": None
                }
            }

        # 4. STANDARD BAR: Fallback for general numeric comparisons
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            return {
                "type": "bar",
                "data": data,
                "config": {
                    "xKey": categorical_cols[0],
                    "yKey": numeric_cols[0],
                    "title": None
                }
            }

    return None


def is_clarification_request(response: str) -> bool:
    """
    Check if the agent's response is asking for clarification rather than providing an answer.
    These responses shouldn't count against the user's query limit.
    """

    response_lower = response.lower()

    # Patterns that indicate the agent is asking for more context
    clarification_patterns = [
        r"could you (please )?(clarify|specify|tell me|provide|share|give me)",
        r"what (specific|particular|kind of|type of)",
        r"which (specific|particular|one|games?|genre)",
        r"can you (be more specific|clarify|tell me more|provide more)",
        r"i('d| would) need (more|additional) (information|context|details)",
        r"to (better |)help you,? i('d| would) need",
        r"(could|would) you (mind |)(sharing|providing|telling)",
        r"what (do you mean|are you looking for|would you like)",
        r"(please |)let me know (which|what|more about)",
        r"are you (asking about|looking for|interested in)",
        r"do you (mean|want|have a specific)",
    ]

    for pattern in clarification_patterns:
        if re.search(pattern, response_lower):
            # Also check if it ends with a question mark (confirming it's asking something)
            if "?" in response:
                return True

    return False


# Request/Response models
class ChatRequest(BaseModel):
    question: str
    conversation_history: Optional[List[Dict[str, str]]] = []
    user_id: Optional[str] = None
    plan: Optional[str] = 'free'


class ChatResponse(BaseModel):
    answer: str
    sql_query: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    chart_config: Optional[Dict[str, Any]] = None
    query_usage: Optional[Dict[str, Any]] = None


class QueryUsageRequest(BaseModel):
    user_id: str
    plan: str


class QueryUsageResponse(BaseModel):
    allowed: bool
    remaining: int
    limit: int
    used: int
    reset_date: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "PlayIntel API",
        "status": "running",
        "version": "1.0.0"
    }


@app.post("/api/query-usage", response_model=QueryUsageResponse)
async def get_query_usage(request: QueryUsageRequest):
    """Check user's query usage and limits."""
    usage = check_query_limit(request.user_id, request.plan)
    return QueryUsageResponse(**usage)


@app.get("/api/stats")
async def get_quick_stats():
    """Get quick market statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM summary_stats LIMIT 1;")
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]

        stats = dict(zip(columns, row)) if row else {}

        cursor.close()
        conn.close()

        return {"stats": stats}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Main conversational AI endpoint.
    Converts natural language questions to SQL and returns insights.
    """
    try:
        # Check query limits if user_id is provided
        query_usage = None
        if request.user_id:
            usage = check_query_limit(request.user_id, request.plan or 'free')
            if not usage['allowed']:
                return ChatResponse(
                    answer=f"You've reached your monthly query limit ({usage['limit']} queries). Your queries will reset on the 1st of next month, or you can upgrade your plan for more queries.",
                    sql_query=None,
                    data=None,
                    query_usage=usage
                )

        # Check if user is responding to a chart offer
        chart_acceptance_phrases = ['yes', 'yeah', 'sure', 'please', 'show me', 'show chart', 'visualize', 'yes please', 'go ahead', 'ok', 'okay']
        question_lower = request.question.lower().strip()

        # Check conversation history for a recent chart offer
        if len(request.conversation_history) >= 2 and question_lower in chart_acceptance_phrases:
            last_assistant_msg = None
            for msg in reversed(request.conversation_history):
                if msg.get('role') == 'assistant':
                    last_assistant_msg = msg.get('content', '')
                    break

            if last_assistant_msg and 'visualize this data as a chart' in last_assistant_msg.lower():
                # User is accepting chart offer - return acknowledgment with flag to show chart
                return ChatResponse(
                    answer="Here's the chart visualization of the data:",
                    sql_query=None,
                    data=None,
                    chart_config={"show_previous": True},  # Signal to frontend to show last chart
                    query_usage=check_query_limit(request.user_id, request.plan or 'free') if request.user_id else None
                )

        # First, determine if this requires database access or is just conversational
        router_prompt = f"""You are PlayIntel AI, a conversational assistant for indie game developers.

Determine if the user's question requires database access or is just a conversational question.

Question types that DON'T need database access (conversational):
- Questions about yourself, your capabilities, or how you work
  Examples: "what can you help me with?", "what can you analyse?", "how do you work?"
- Greetings, thanks, feedback about responses
  Examples: "thanks!", "hello", "that was helpful"
- General game development advice not requiring specific data
  Examples: "should I add multiplayer?", "how do I market my game?"
- Questions about the format of your responses
  Examples: "why do you use emojis?", "do you always give insights?"
- Clarification questions about previous answers
  Examples: "what do you mean by that?", "can you explain more?"
- Questions about external information NOT in our database (requires web search):
  Examples: "what's BlueTwelve Studio's website?", "developer contact info", "studio Twitter/social media"
  Examples: "latest news about Larian Studios", "when is the next update for Hades?"
  Keywords: website, URL, contact, email, Twitter, Discord, social media, news, announcement

Question types that NEED database access (analytical):
- Specific questions about games, developers, publishers, or market data FROM OUR DATABASE
  Examples: "top 10 games by revenue", "show me Valve's games", "what's the average price?"
- Requests for rankings, statistics, comparisons
  Examples: "compare indie vs AAA games", "which genre is most profitable?"
- Questions asking for actual data with "show me", "what are the", "which games", "top 10", etc.
  Examples: "show me games under $10", "what are the best rated games?"
- NOTE: Questions about websites, contact info, or external URLs do NOT need database - use conversational path

User's question: "{request.question}"

Respond with ONLY valid JSON:
{{
    "needs_database": true/false,
    "reasoning": "brief explanation"
}}"""

        router_response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            messages=[{"role": "user", "content": router_prompt}]
        )

        import json
        router_result = json.loads(router_response.content[0].text.strip())

        # If it's conversational, respond without database access
        if not router_result.get("needs_database", True):
            # Load industry knowledge for conversational responses
            from pathlib import Path
            industry_knowledge_path = Path(__file__).parent / "indie_game_industry_knowledge.txt"
            industry_knowledge = ""
            if industry_knowledge_path.exists():
                industry_knowledge = industry_knowledge_path.read_text()

            conversational_messages = []
            for msg in request.conversation_history:
                conversational_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            conversational_messages.append({
                "role": "user",
                "content": request.question
            })

            conversational_system = f"""You help indie game developers succeed in the Steam market.

INDUSTRY KNOWLEDGE BASE:
{industry_knowledge}

CRITICAL - NEVER DO THESE:
- NEVER introduce yourself ("I'm an analyst", "As an expert", "With X years experience")
- NEVER use filler phrases ("Great question!", "Certainly!", "I'd be happy to", "Absolutely!")
- NEVER say "Looking at the data", "Let me check", "Based on my analysis"
- NEVER mention your experience, credentials, or how long you've been doing this

ALWAYS DO THESE:
- Start with the answer or key point immediately
- Use "you/your" when addressing the user
- Be direct and conversational
- Draw from the industry knowledge above when giving advice
- Reference real examples when relevant (Hades, Stardew Valley, etc.)

WHEN ASKED WHAT YOU CAN HELP WITH:
"I can help with Steam market data, pricing strategy, genre analysis, and general game dev advice - funding, marketing, launch timing, that kind of thing. What are you working on?"

ADVICE APPROACH:
- Give specific, actionable advice based on industry patterns
- Reference success stories and cautionary tales when relevant
- Be honest about risks and challenges
- Help them think through decisions, don't just validate

TONE:
Direct, helpful, knowledgeable. Like a friend who's shipped games and knows the industry. No corporate speak, no filler, no self-promotion.

WEB SEARCH:
You have access to web search. Use it when users ask about:
- Developer/publisher websites, contact info, or social media
- Current news about games or studios
- Information not in your knowledge (release dates, updates, etc.)
- Anything requiring real-time or external data

LINK FORMATTING (CRITICAL):
NEVER output raw URLs or malformed markdown like: example.com](https://example.com)

ALWAYS use proper markdown: [Display Name](https://full-url)

Display name rules:
- Game → use game name: [Stray](https://store.steampowered.com/app/1332010/Stray/)
- Studio → use studio name: [BlueTwelve Studio](https://bluetwelvestudio.com)
- Steam page → [View on Steam](https://store.steampowered.com/app/XXXXX)
- Social media → [Twitter](https://twitter.com/handle) or [Discord](https://discord.gg/xxx)

If display name is unclear, infer from the domain. Never show URLs as text."""

            # Use web search tool for conversational responses
            conversational_response = anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                system=conversational_system,
                messages=conversational_messages,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3}]
            )

            # Extract text from response (may include tool use results)
            response_text = ""
            for block in conversational_response.content:
                if hasattr(block, 'text'):
                    response_text += block.text

            # Only count against quota if it's a real answer, not a clarification request
            if request.user_id and not is_clarification_request(response_text):
                increment_query_count(request.user_id)
                query_usage = check_query_limit(request.user_id, request.plan or 'free')
            elif request.user_id:
                # Still get usage info but don't increment
                query_usage = check_query_limit(request.user_id, request.plan or 'free')

            return ChatResponse(
                answer=response_text,
                sql_query=None,
                data=None,
                query_usage=query_usage
            )

        # If it needs database access, proceed with SQL generation
        # Load analytical knowledge base
        from pathlib import Path
        knowledge_base_path = Path(__file__).parent / "alex_knowledge_base.txt"
        analytical_knowledge = ""
        if knowledge_base_path.exists():
            analytical_knowledge = knowledge_base_path.read_text()

        # Build conversation context for Claude
        system_prompt = f"""You generate SQL queries for Steam market data analysis.

ANALYTICAL CONTEXT:
{analytical_knowledge}

DATABASE SCHEMA:
{get_database_schema()}

QUERY GUIDELINES:
1. Write precise PostgreSQL queries on a single line
2. ALWAYS include ALL fields the user asks for (if they ask for ratings, SELECT rating_percentage!)
3. Use appropriate filters (exclude games with 0 owners when looking for successful examples)
4. Consider price tiers: Free, $5-10 (Low), $10-20 (Medium), $20-50 (Premium), $50+ (AAA)

LIMIT CLAUSE RULES:
- "top 5", "top 10" → Use LIMIT 5, LIMIT 10
- "all", "every", "list all" → DO NOT use LIMIT
- Default: LIMIT 100 for general queries

AGGREGATE QUERIES:
When user asks for "average", "typical":
✅ Use AVG() across ALL matching games
❌ Don't select individual games then show results

Price range rules:
- "$15" → WHERE price_usd BETWEEN 14 AND 16
- "$20" → WHERE price_usd BETWEEN 19 AND 21
- "around $X" → WHERE price_usd BETWEEN X-2 AND X+2

Respond ONLY with valid JSON:
{{
    "sql_query": "SELECT ... FROM ... WHERE ...",
    "explanation": "Brief explanation",
    "recommendation": "Brief recommendation"
}}
"""

        # Build message history
        messages = []
        for msg in request.conversation_history:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        messages.append({
            "role": "user",
            "content": request.question
        })

        # Call Claude AI
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2000,
            system=system_prompt,
            messages=messages
        )

        # Parse Claude's response
        ai_response = response.content[0].text

        # Try to parse JSON response
        sql_query = None
        data = None
        chart_config = None
        user_answer = ai_response

        try:
            # Try to parse as JSON
            import json
            import re

            # Try direct JSON parse first
            cleaned_response = ai_response.strip()

            # If response contains JSON wrapped in text, extract it
            if not cleaned_response.startswith('{'):
                # Look for JSON object in the response
                json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
                if json_match:
                    cleaned_response = json_match.group(0)

            # Fix common JSON issues from Claude: unescaped newlines in string values
            # Replace literal newlines inside quoted strings with spaces
            def fix_json_newlines(text):
                result = []
                in_string = False
                escape_next = False

                for i, char in enumerate(text):
                    if escape_next:
                        result.append(char)
                        escape_next = False
                    elif char == '\\':
                        result.append(char)
                        escape_next = True
                    elif char == '"':
                        result.append(char)
                        in_string = not in_string
                    elif char == '\n' and in_string:
                        result.append(' ')  # Replace newline with space inside strings
                    else:
                        result.append(char)

                return ''.join(result)

            cleaned_response = fix_json_newlines(cleaned_response)
            response_json = json.loads(cleaned_response)

            sql_query = response_json.get("sql_query")
            explanation = response_json.get("explanation", "")
            recommendation = response_json.get("recommendation", "")

            # Execute SQL query if provided
            if sql_query:
                print(f"Generated SQL: {sql_query}")  # Debug logging
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute(sql_query)
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]

                    # Convert to list of dicts, handling Decimal and datetime types
                    from decimal import Decimal
                    from datetime import datetime, date

                    def convert_types(obj):
                        if isinstance(obj, Decimal):
                            return float(obj)
                        elif isinstance(obj, (datetime, date)):
                            return obj.isoformat()
                        return obj

                    data = [
                        {col: convert_types(val) for col, val in zip(columns, row)}
                        for row in rows
                    ]

                    cursor.close()
                    conn.close()

                    # Build user-friendly response with actual data
                    if data and len(data) > 0:
                        # Analyze if visualization would be beneficial
                        chart_config = analyze_data_for_visualization(data, request.question)
                        print(f"Chart analysis result: {chart_config is not None}, type: {chart_config.get('type') if chart_config else 'None'}")
                        print(f"Data columns: {list(data[0].keys()) if data else 'No data'}")

                        # Make a second Claude call to interpret the results
                        interpretation_prompt = get_interpretation_prompt(request.question, data, len(data))

                        interpretation_response = anthropic_client.messages.create(
                            model="claude-3-haiku-20240307",
                            max_tokens=1500,
                            messages=[{"role": "user", "content": interpretation_prompt}]
                        )

                        user_answer = interpretation_response.content[0].text

                        # Check if user wants data displayed (table/export) or if query returns game-level details
                        question_lower = request.question.lower()

                        # Keywords that indicate user wants to see/export data
                        table_keywords = ['table', 'list', 'show me all', 'show all', 'give me a list', 'export', 'csv', 'spreadsheet', 'detailed breakdown']

                        # Keywords that indicate query returns game-level data worth showing
                        detail_keywords = ['top', 'best', 'worst', 'compare', 'vs', 'versus', 'examples', 'games like', 'similar to', 'highest', 'lowest']

                        wants_table = any(kw in question_lower for kw in table_keywords)
                        has_detail_query = any(kw in question_lower for kw in detail_keywords)

                        # Keep data if: user asked for table/export, OR query returns game details, OR data has game names
                        has_game_names = data and len(data) > 0 and any(key in str(data[0].keys()).lower() for key in ['name', 'game', 'title'])

                        # Only hide data for pure aggregate queries (averages, counts, totals)
                        if not (wants_table or has_detail_query or has_game_names):
                            data = None  # Don't send raw data for aggregate-only queries

                        # If we have chart data, add offer to user's response
                        if chart_config and len(data or []) >= 3:
                            # Only offer chart if not already explicitly requested
                            chart_keywords = ['chart', 'graph', 'plot', 'visualize', 'visualization']
                            if not any(kw in question_lower for kw in chart_keywords):
                                user_answer += "\n\n*Would you like me to visualize this data as a chart?*"
                    else:
                        # No data - provide helpful response without technical details
                        user_answer = f"I couldn't find any games matching those criteria in the dataset. This could mean:\n\n• The filters were too specific\n• Data quality issues (many games have incomplete info)\n• The combination you're looking for is rare\n\nTry broadening your criteria or asking about a different aspect of the data."

                except Exception as db_error:
                    print(f"Database error: {db_error}")

                    # Try to fix the query and retry
                    fix_prompt = f"""The following SQL query failed with an error:

SQL Query:
{sql_query}

Error:
{str(db_error)}

Database Schema:
{get_database_schema()}

Please fix the SQL query to resolve this error. Return ONLY valid JSON with the corrected query.

Response format:
{{
    "sql_query": "SELECT ... FROM ... WHERE ...",
    "explanation": "I fixed the query by..."
}}"""

                    try:
                        fix_response = anthropic_client.messages.create(
                            model="claude-3-haiku-20240307",
                            max_tokens=1000,
                            messages=[{"role": "user", "content": fix_prompt}]
                        )

                        fixed_json = json.loads(fix_json_newlines(fix_response.content[0].text.strip()))
                        fixed_sql = fixed_json.get("sql_query")

                        if fixed_sql:
                            # Retry with fixed query
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute(fixed_sql)
                            rows = cursor.fetchall()
                            columns = [desc[0] for desc in cursor.description]

                            from decimal import Decimal
                            from datetime import datetime, date

                            def convert_types(obj):
                                if isinstance(obj, Decimal):
                                    return float(obj)
                                elif isinstance(obj, (datetime, date)):
                                    return obj.isoformat()
                                return obj

                            data = [
                                {col: convert_types(val) for col, val in zip(columns, row)}
                                for row in rows
                            ]

                            cursor.close()
                            conn.close()

                            # Update sql_query for return value
                            sql_query = fixed_sql

                            # Interpret results if successful
                            if data and len(data) > 0:
                                # Analyze for visualization on retry path
                                chart_config = analyze_data_for_visualization(data, request.question)

                                interpretation_prompt = get_interpretation_prompt(request.question, data, len(data))

                                interpretation_response = anthropic_client.messages.create(
                                    model="claude-3-haiku-20240307",
                                    max_tokens=2000,
                                    messages=[{"role": "user", "content": interpretation_prompt}]
                                )

                                user_answer = interpretation_response.content[0].text

                                # Check if user wants data displayed (table/export) or if query returns game-level details
                                question_lower = request.question.lower()

                                # Keywords that indicate user wants to see/export data
                                table_keywords = ['table', 'list', 'show me all', 'show all', 'give me a list', 'export', 'csv', 'spreadsheet', 'detailed breakdown']

                                # Keywords that indicate query returns game-level data worth showing
                                detail_keywords = ['top', 'best', 'worst', 'compare', 'vs', 'versus', 'examples', 'games like', 'similar to', 'highest', 'lowest']

                                wants_table = any(kw in question_lower for kw in table_keywords)
                                has_detail_query = any(kw in question_lower for kw in detail_keywords)

                                # Keep data if: user asked for table/export, OR query returns game details, OR data has game names
                                has_game_names = data and len(data) > 0 and any(key in str(data[0].keys()).lower() for key in ['name', 'game', 'title'])

                                # Only hide data for pure aggregate queries (averages, counts, totals)
                                if not (wants_table or has_detail_query or has_game_names):
                                    data = None  # Don't send raw data for aggregate-only queries

                                # If we have chart data, add offer to user's response
                                if chart_config and len(data or []) >= 3:
                                    chart_keywords = ['chart', 'graph', 'plot', 'visualize', 'visualization']
                                    if not any(kw in question_lower for kw in chart_keywords):
                                        user_answer += "\n\n*Would you like me to visualize this data as a chart?*"
                            else:
                                user_answer = "No results found for your query."
                        else:
                            user_answer = "I encountered an error processing your request. Could you try rephrasing your question?"

                    except Exception as retry_error:
                        print(f"Retry failed: {retry_error}")
                        user_answer = "I'm having trouble processing that request. Could you try asking in a different way?"
            else:
                # No SQL query, just use explanation and recommendation
                user_answer = f"{explanation}\n\n{recommendation}" if recommendation else explanation

        except json.JSONDecodeError:
            # Not JSON, use the raw response
            user_answer = ai_response

        # Only count against quota if it's a real answer, not a clarification request
        if request.user_id and not is_clarification_request(user_answer):
            increment_query_count(request.user_id)
            query_usage = check_query_limit(request.user_id, request.plan or 'free')
        elif request.user_id:
            # Still get usage info but don't increment
            query_usage = check_query_limit(request.user_id, request.plan or 'free')

        return ChatResponse(
            answer=user_answer,
            sql_query=sql_query,
            data=data,
            chart_config=chart_config,
            query_usage=query_usage
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/api/sample-questions")
async def get_sample_questions():
    """Get sample questions users can ask."""
    return {
        "questions": [
            {
                "category": "Pricing Strategy",
                "questions": [
                    "What's the average playtime for games priced at $15?",
                    "Show me the most successful price points",
                    "What's the best price for a 20-hour game?"
                ]
            },
            {
                "category": "Market Research",
                "questions": [
                    "What rating percentage do I need to compete in the $20-30 tier?",
                    "How many owners do successful indie developers have on average?",
                    "What's considered good value for money?"
                ]
            },
            {
                "category": "Developer Insights",
                "questions": [
                    "Show me the top 10 indie developers by total owners",
                    "What's the average number of games before a developer's breakout hit?",
                    "Compare developers with 1-3 games vs 4+ games"
                ]
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
