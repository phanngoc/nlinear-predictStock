# AnswerMe - News Summary Chatbot

AI-powered news aggregation and summary system with keyword tracking and chat interface.

## Features

- 🔐 User authentication (JWT)
- 🏷️ Keyword subscription (5 for free, unlimited for premium)
- 📰 Daily AI-generated summaries
- 💬 Thread-based chat with Q&A
- 🔗 Access to original news sources

## Quick Start

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your settings

# Setup PostgreSQL database
createdb newsdb

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload
```

API available at http://localhost:8000

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Setup environment
cp .env.local.example .env.local

# Start dev server
npm run dev
```

App available at http://localhost:3000

## API Endpoints

### Auth
- `POST /api/auth/register` - Register
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Current user

### Keywords
- `GET /api/keywords` - List keywords
- `POST /api/keywords` - Add keyword
- `DELETE /api/keywords/{id}` - Delete keyword

### Threads
- `GET /api/threads` - List threads
- `GET /api/threads/today` - Get/generate today's summary
- `GET /api/threads/{id}` - Get thread
- `DELETE /api/threads/{id}` - Delete thread

### Chat
- `POST /api/threads/{id}/query` - Ask question

## User Types

| Feature | Free | Premium | Admin |
|---------|------|---------|-------|
| Keywords | 5 | Unlimited | Unlimited |
| Thread History | 30 days | Full | Full |
| Daily Queries | 10 | Unlimited | Unlimited |

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, LlamaIndex, PostgreSQL
- **Frontend**: Next.js, Zustand, TailwindCSS, shadcn/ui
