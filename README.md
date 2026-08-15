# CLIVE — Your Signal in the AI Noise

> **CLIVE** is a personal AI intelligence platform that continuously collects important developments from reputable first-party AI company blogs, RSS/Atom feeds, research papers, and public engineering pages, normalizes, deduplicates with RapidFuzz, classifies and extracts structured intelligence with server-side Gemini AI models, ranks with a personalized multi-factor algorithm, and delivers an executive mobile-first intelligence radar with spring-physics swipe gestures.

---

## ⚡ Core UX & Features

- **Mobile-First Experience (390×844 Target)**: Centered and optimized for mobile devices with an interactive desktop frame wrapper.
- **RADAR Swipe Deck**:
  - **Swipe RIGHT** $\rightarrow$ **Interested**: Increases personalized topic multipliers in real-time.
  - **Swipe LEFT** $\rightarrow$ **Skip**: Gently discounts topic weights.
  - **Bookmark** $\rightarrow$ **Save**: Strong positive signal and saves to your permanent briefing collection.
  - **Tap Card** $\rightarrow$ **Story Detail**: Opens executive summary, "Why It Matters" structured takeaways, and multi-factor score gauges.
  - **Read Source** $\rightarrow$ **Original Publication**: Opens the official lab post directly.
- **Isolated Multi-Factor Ranking Engine**:
  $$\text{Score} = (0.40 \times \text{Importance}) + (0.30 \times \text{Relevance}) + (0.20 \times \text{Recency}) + (0.10 \times \text{Novelty}) + \text{Breaking Boost}$$
- **Multi-Tier RapidFuzz Deduplication**: Canonicalizes URLs, removes tracking parameters (`utm_*`, `ref`, `fbclid`), compares normalized titles, checks topic/company context within time windows, and prioritizes first-party lab sources.
- **Server-Side AI Pipeline**: Google Gemini models via environment variables (`GEMINI_API_KEY`, `GEMINI_MODEL`) with automatic heuristic rule-engine fallback for zero-downtime operation.
- **Robust Ingestion Engine**: Built with `feedparser`, `httpx`, `trafilatura`, `BeautifulSoup4`, and `tenacity` retries. One failing feed never stops a scan.
- **SQLite with WAL Mode**: Concurrent, crash-resilient write-ahead logging with clean SQLAlchemy abstractions for future PostgreSQL migration.

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Python 3.11/3.12 + FastAPI + Uvicorn
- **ORM & DB**: SQLAlchemy 2.0 + SQLite (WAL Mode `PRAGMA journal_mode=WAL;`)
- **Validation**: Pydantic v2 + Pydantic Settings
- **Ingestion**: `feedparser`, `httpx`, `trafilatura`, `beautifulsoup4`, `tenacity`
- **Deduplication**: `rapidfuzz`
- **Scheduler**: `APScheduler`
- **AI**: `google-genai` (Gemini Flash / Flash Lite) + Heuristic Fallback Engine
- **Testing**: `pytest`, `pytest-asyncio`

### Frontend
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS v3 (Cyber-Luxe Cyberpunk Cyan `#00F0FF` + Mint `#10E760` + Deep Space Obsidian `#070A0F`)
- **Physics & Motion**: Framer Motion (Drag spring physics, swipe rotation, feedback stamps)
- **Data Fetching & Cache**: TanStack React Query v5
- **Routing**: React Router DOM v6
- **Icons**: Lucide React

---

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to backend and create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt

# Run FastAPI Server (auto-seeds default sources and triggers first ingestion)
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive OpenAPI Swagger UI is available at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install packages
npm install

# Start Vite Development Server
npm run dev
```

Visit `http://localhost:5173` in your browser.

---

## 🧪 Testing

Run backend test suite:
```bash
pytest -v backend/tests
```

Run launch checklist verification script:
```bash
python verify_launch_checklist.py
```
