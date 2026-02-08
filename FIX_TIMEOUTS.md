# Fix Timeout Issues - Action Plan

## Problem
20% of API requests taking >20 seconds and timing out

## Investigation Steps

### 1. Add Timing Logs to Backend

Edit `/Users/tosdaboss/playintel/backend/main.py`:

```python
import time

# In the /api/chat endpoint, add timing:
@app.post("/api/chat")
async def chat(request: ChatRequest):
    start_time = time.time()
    
    # ... existing code ...
    
    # After Claude routing call
    routing_time = time.time() - start_time
    print(f"⏱️ Routing took: {routing_time:.2f}s")
    
    # After SQL generation
    sql_gen_time = time.time() - start_time - routing_time
    print(f"⏱️ SQL generation took: {sql_gen_time:.2f}s")
    
    # After DB query
    db_query_time = time.time() - start_time - routing_time - sql_gen_time
    print(f"⏱️ Database query took: {db_query_time:.2f}s")
    
    # After interpretation
    total_time = time.time() - start_time
    print(f"⏱️ TOTAL: {total_time:.2f}s")
```

### 2. Apply Database Indexes

```bash
# Run the optimization SQL
psql postgresql://postgres:YOUR_PASSWORD@localhost:5432/steam_apps_db \
  -f /Users/tosdaboss/optimize_tag_search.sql
```

This will:
- Install pg_trgm extension
- Create GIN indexes on top_tags and genres
- Speed up ILIKE queries 5-10x

### 3. Increase Frontend Timeout

Edit `/Users/tosdaboss/playintel/frontend/src/App.jsx`:

```javascript
// Change timeout from 20s to 30s
const response = await fetch('http://localhost:8000/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question: userMessage, conversation_history: cleanHistory }),
  signal: AbortSignal.timeout(30000)  // 30 seconds
})
```

### 4. Expected Timing Breakdown

Good performance:
- Routing: 0.5-1s
- SQL generation: 1-3s
- Database query: 0.1-1s
- Interpretation: 1-3s
- **Total: 3-8 seconds** ✅

Bad performance (needs fixing):
- Total: >15 seconds ❌

### 5. Common Causes & Fixes

| Cause | Fix |
|-------|-----|
| Missing indexes | Run optimize_tag_search.sql |
| Complex SQL | Add query complexity limits |
| Claude API slow | Use Claude Haiku (you already do) ✅ |
| Large result sets | Add LIMIT to all queries |

## Timeline

- Apply indexes: 10 minutes
- Add timing logs: 30 minutes
- Test and verify: 1 hour
- **Total: 2 hours**

## Success Criteria

After fixes:
- ✅ <10% timeout rate
- ✅ Average response time <10s
- ✅ No query takes >15s

