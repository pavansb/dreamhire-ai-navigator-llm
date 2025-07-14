# DreamHire AI Navigator LLM Backend

FastAPI backend service for DreamHire AI Navigator - AI-powered recruitment platform.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## API Endpoints

- **Health Check:** `GET /api/ping`
- **Root:** `GET /`
- **API Documentation:** `GET /docs` (Swagger UI)
- **ReDoc Documentation:** `GET /redoc`

## Development

The server runs on `http://localhost:8000` by default.

### Project Structure

```
app/
├── main.py              # FastAPI application entry point
├── core/
│   ├── config.py        # Configuration settings
│   └── database.py      # MongoDB connection
├── api/
│   └── routes/
│       └── ping.py      # Health check endpoint
└── models/              # Data models and schemas
```

## Environment Variables

Create a `.env` file in the root directory to override default settings:

```env
MONGODB_URI=your_mongodb_connection_string
DATABASE_NAME=your_database_name
``` 