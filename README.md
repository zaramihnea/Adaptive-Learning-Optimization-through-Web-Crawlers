# Adaptive Learning Optimization through Web Crawlers

**Project 16 — Educational Technology and Web Information Retrieval**  
Distributed Systems (PCD) — Master Year 1, Semester 2

A crawler-based educational content pipeline that retrieves, filters, classifies, and recommends online resources for a given learner profile (topic, difficulty level, learning goal, language).

---

## Architecture

```
Project/
├── crawler/          # Scrapy crawler + FastAPI backend
│   ├── api/          # REST API (POST /crawl, GET /crawl, NLP endpoints)
│   ├── crawler/      # Scrapy spider, pipelines, settings
│   ├── db/           # SQLAlchemy models and session
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── run_crawl.py  # subprocess entry point for Scrapy
├── pipeline/         # NLP classifier + TF-IDF recommender engine
│   ├── nlp_classifier.py
│   └── recommender_engine.py
└── frontend/         # Static HTML/JS UI served by nginx
    ├── index.html
    ├── nginx.conf
    └── Dockerfile
```

### Components

| Component | Description |
|-----------|-------------|
| **Scrapy spider** | Crawls from seed URLs, follows topic-relevant links across domains, respects robots.txt and rate limits |
| **PostgreSQL** | Stores documents (global dedup) and crawl runs (per learner profile) |
| **NLP Classifier** | Keyword + word-count heuristic to label difficulty (beginner / intermediate / advanced) |
| **Recommender Engine** | TF-IDF cosine similarity between learner goal and document body, with difficulty penalty |
| **FastAPI** | Synchronous `POST /crawl` (crawl + return results) and `GET /crawl` (fetch cached results) |
| **Frontend** | Single-page UI for submitting crawl requests and viewing ranked results |

### Database Schema

```
documents           — global content store (URL-deduplicated, SHA-256 hash)
crawl_runs          — one row per learner profile session
crawl_run_documents — join table linking documents to runs, stores per-profile relevance_score
```

---

## Requirements

- Docker + Docker Compose (recommended)
- Or: Python 3.11+, PostgreSQL 16

---

## Quickstart (Docker)

```bash
git clone https://github.com/zaramihnea/Adaptive-Learning-Optimization-through-Web-Crawlers.git
cd Adaptive-Learning-Optimization-through-Web-Crawlers

# Copy and configure environment
cp crawler/.env.example crawler/.env

# Build and start all services (db + api + frontend)
cd crawler
docker-compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| PostgreSQL | localhost:5434 |

---

## Quickstart (Local / Virtual Environment)

```bash
cd crawler

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set DATABASE_URL to your local postgres

# Start postgres via Docker only
docker-compose up -d db

# Run the API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

Copy `crawler/.env.example` to `crawler/.env` and edit as needed:

```env
DATABASE_URL=postgresql://crawler:password@localhost:5434/educrawl
CRAWL_DELAY=1.5        # seconds between requests (rate limiting)
MAX_PAGES=500          # hard cap on pages per crawl session
LOG_LEVEL=INFO
```

Key Scrapy settings (in `crawler/crawler/settings.py`):

| Setting | Default | Description |
|---------|---------|-------------|
| `ROBOTSTXT_OBEY` | `True` | Respect robots.txt |
| `DOWNLOAD_DELAY` | `1.5s` | Delay between requests |
| `CONCURRENT_REQUESTS_PER_DOMAIN` | `1` | Max parallel requests per domain |
| `CLOSESPIDER_PAGECOUNT` | `500` | Hard page cap per run |

---

## Running an Experiment

### Via the Frontend

1. Open http://localhost:3000
2. Turn **Mock mode OFF**
3. Fill in the form and click **POST /crawl**

### Via the API directly

```bash
curl -X POST http://localhost:8000/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "seed_urls": ["https://realpython.com", "https://docs.python.org/3/tutorial/"],
    "topic": "python",
    "learner_level": "beginner",
    "learner_goal": "learn python functions and data structures",
    "language": "en",
    "depth": 2,
    "max_items": 30
  }'
```

Fetch cached results from a previous run:

```bash
curl "http://localhost:8000/crawl?topic=python&learner_level=beginner&learner_goal=learn+python+functions+and+data+structures"
```

### Example Inputs

| Topic | Seed URLs | Level | Goal |
|-------|-----------|-------|------|
| Python | `https://realpython.com` | beginner | learn python basics |
| JavaScript | `https://javascript.info` | beginner | understand javascript fundamentals |
| Machine Learning | `https://machinelearningmastery.com/start-here/` | intermediate | understand neural networks |
| Web Dev | `https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous` | intermediate | master async await and promises |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/crawl` | Run a new crawl and return ranked results |
| `GET` | `/crawl` | Fetch results from a previous matching run |
| `GET` | `/documents/unclassified` | NLP: fetch unclassified documents |
| `PATCH` | `/documents/{id}` | NLP: write back difficulty + topic label |
| `PATCH` | `/runs/{run_id}/documents/{doc_id}/score` | NLP: write relevance score |

Full interactive docs: http://localhost:8000/docs

---

## NLP Pipeline

The pipeline runs automatically after each crawl (inside the API process):

1. **Classification** (`pipeline/nlp_classifier.py`) — assigns `difficulty` (beginner / intermediate / advanced) based on vocabulary complexity and document length
2. **Ranking** (`pipeline/recommender_engine.py`) — computes TF-IDF cosine similarity between the learner goal and each document body, then applies a difficulty-match penalty

To run the pipeline manually:

```bash
cd /path/to/project
python pipeline/nlp_classifier.py
python pipeline/recommender_engine.py  # edit run_id in __main__ block
```

---

## Ethics and Compliance

- **robots.txt**: enforced via Scrapy's `ROBOTSTXT_OBEY = True`
- **Rate limiting**: 1.5s delay + max 1 concurrent request per domain
- **User-Agent**: identifies the bot as an academic research crawler with contact email
- **Copyright**: content is stored for research/evaluation purposes only, not redistributed
- **Deduplication**: SHA-256 content hash prevents storing duplicate pages

---

## Dependencies

See `crawler/requirements.txt`. Key packages:

```
scrapy==2.11.2
Twisted==24.3.0
trafilatura==1.12.0
sqlalchemy==2.0.36
fastapi==0.115.0
scikit-learn>=1.3.0
langdetect==1.0.9
psycopg2-binary>=2.9.9
```

> **Note:** Twisted is pinned to 24.3.0 — Twisted 26.x is incompatible with Scrapy 2.11.2.

---

## Team

| Student | Role |
|---------|------|
| Zara Mihnea-Tudor | Data & Infrastructure Lead — crawler, database schema, API |
| Mihoc Roxana | NLP Lead — classifier, recommender engine |
| Roman Iulian | Frontend & Evaluation Lead — UI, evaluation scripts |
