# PlayIntel - AI-Powered Steam Market Intelligence

PlayIntel helps indie game developers make data-driven decisions using conversational AI and real Steam market data.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL with steam_apps_db
- Anthropic Claude API key

### Setup

1. **Install Backend Dependencies**
```bash
cd playintel/backend
pip3 install -r requirements.txt
```

2. **Configure Environment**
```bash
# Edit backend/.env and add your Claude API key
nano backend/.env
```

3. **Run Backend Server**
```bash
cd backend
python3 main.py
```

The API will be available at: http://localhost:8000

### Test the API

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

### Sample API Calls

**Get quick stats:**
```bash
curl http://localhost:8000/api/stats
```

**Ask a question:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the average playtime for games priced at $15?"
  }'
```

## Project Structure

```
playintel/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment configuration
│   └── .env.example         # Example configuration
├── frontend/                # React frontend (coming next)
└── README.md               # This file
```

## Features

- **Conversational AI**: Ask questions in natural language
- **Real Data**: 4,928 games, 3,253 developers, 2,359 publishers
- **Market Insights**: Pricing, playtime, reviews, engagement
- **Developer Intelligence**: Benchmarks, comparisons, recommendations

## API Endpoints

- `GET /` - Health check
- `GET /api/stats` - Quick market statistics
- `POST /api/chat` - Conversational AI query
- `GET /api/sample-questions` - Sample questions to ask

## Next Steps

1. Add your Claude API key to `backend/.env`
2. Test the backend API
3. Build the frontend React app
4. Deploy to production

## Support

Questions? Issues? Contact: hello@playintel.net
