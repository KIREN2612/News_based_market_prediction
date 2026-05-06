---
title: Signal News Based Market Predictor
emoji: 🏆
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

---
title: NSE Finance Sentiment Signal
emoji: 📈
colorFrom: green
colorTo: blue
sdk: docker
pinned: true
---

# 📊 Finance News Sentiment System

> Real-time conviction signal layer for Indian retail investors — built targeting [StockGro/Stoxo](https://www.stockgro.club/)'s core pain point: users drowning in unverified financial news with no clear signal to act on.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green?style=flat-square&logo=fastapi)
![FinBERT](https://img.shields.io/badge/Model-FinBERT-purple?style=flat-square)
![SQLite](https://img.shields.io/badge/DB-SQLite-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)

---

## 🧠 The Problem

Indian retail investors make decisions based on scattered, unverified news from WhatsApp groups, Telegram channels, and 20+ news sites — all saying different things. None of the major platforms (Tickertape, Sensibull, StockGro) have a real-time, per-ticker sentiment signal with source credibility scoring built on actual NLP.

The result: **90% of retail users lose conviction before acting** — not because of lack of data, but because of too much noise.

---

## ✅ What This System Does

- Ingests live NSE/BSE stock news headlines every **3 minutes** automatically
- Scores each headline using **FinBERT** — a transformer pretrained on financial text
- Weights sentiment by **source credibility** (Moneycontrol/ET score higher than unknown Telegram channels)
- Stores results in a structured database per ticker
- Serves a clean conviction signal via **REST API** with **in-memory caching**
- Designed to handle concurrent users without breaking

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EXTERNAL SOURCES                      │
│   NewsAPI (ET, Moneycontrol, Reuters)  │  Credibility   │
│                                           Score List    │
└────────────────────┬────────────────────────────────────┘
                     │ every 3 minutes
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  INGESTION PIPELINE                      │
│                                                          │
│   APScheduler ──► fetch_headlines()                      │
│                        │                                 │
│                        ▼                                 │
│               FinBERT (batch inference)                  │
│                        │                                 │
│              confidence × source_score                   │
│                  = weighted_score                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                     STORAGE LAYER                        │
│                                                          │
│   SQLite DB  ◄──────────────────►  In-memory Cache      │
│   (persistent)                      (60s TTL/ticker)    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                    SERVING LAYER                         │
│                                                          │
│   FastAPI  ──►  GET /sentiment/{ticker}                  │
│                 GET /health                              │
│                                                          │
│   Cache hit → return instantly (<1ms)                    │
│   Cache miss → query DB → fill cache → return            │
└─────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
finbert-sentiment/
│
├── app/
│   ├── main.py          # FastAPI app, lifespan, endpoints
│   ├── scheduler.py     # APScheduler + news fetching + pipeline
│   ├── sentiment.py     # FinBERT loading + inference + label mapping
│   ├── database.py      # SQLite connection, schema, insert, fetch
│   └── cache.py         # In-memory cache with TTL
│
├── model/               # FinBERT weights (auto-downloaded on first run)
├── .env                 # API keys (never committed)
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🗃️ Database Schema

```sql
CREATE TABLE sentiment_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker          TEXT,       -- e.g. "INFY"
    headline        TEXT,       -- raw news headline
    source          TEXT,       -- e.g. "Moneycontrol"
    source_score    REAL,       -- credibility weight 0.0–1.0
    sentiment       TEXT,       -- "bullish" / "bearish" / "neutral"
    confidence      REAL,       -- FinBERT confidence 0.0–1.0
    weighted_score  REAL,       -- confidence × source_score
    fetched_at      DATETIME    -- when the headline was ingested
);
```

---

## 🔌 API Reference

### `GET /health`
Returns system status.

```json
{"status": "ok"}
```

### `GET /sentiment/{ticker}`
Returns the latest sentiment results for a given NSE ticker.

**Example:** `GET /sentiment/INFY`

```json
{
  "source": "cache",
  "data": {
    "ticker": "INFY",
    "rows": [
      [1, "INFY", "Infosys posts record Q4 profits", "Moneycontrol", 0.9, "bullish", 0.96, 0.86, "2026-05-06 11:35:41"]
    ]
  }
}
```

**Response fields:**
| Field | Description |
|---|---|
| `source` | `"cache"` or `"database"` — tells you if result was served from cache |
| `sentiment` | `bullish` / `bearish` / `neutral` |
| `confidence` | FinBERT confidence score (0.0–1.0) |
| `source_score` | Credibility weight of the news source |
| `weighted_score` | `confidence × source_score` — the final conviction signal |

---

## ⚙️ How to Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/KIREN2612/finbert-sentiment.git
cd finbert-sentiment
```

**2. Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # Mac/Linux
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Add your NewsAPI key**

Create a `.env` file in the root:
```
NEWS_API_KEY=your_newsapi_key_here
```
Get a free key at [newsapi.org](https://newsapi.org)

**5. Run the server**
```bash
uvicorn app.main:app --reload
```

FinBERT (~500MB) downloads automatically on first run.

**6. Test it**
```bash
# Check health
curl http://127.0.0.1:8000/health

# Get INFY sentiment
curl http://127.0.0.1:8000/sentiment/INFY
```

Or open `http://127.0.0.1:8000/docs` for the interactive API explorer.

---

## 🔍 Source Credibility Scoring

Not all news is equal. The system weights sentiment by source reliability — a core India-specific insight no major platform has built properly.

| Tier | Sources | Score |
|---|---|---|
| Tier 1 | Moneycontrol, Economic Times, Reuters, Bloomberg | 0.85–0.9 |
| Tier 2 | Business Standard, Mint, NDTV Profit, BusinessLine | 0.75–0.85 |
| Tier 3 | Unknown / unverified sources | 0.4 |

A 95% confident bullish signal from a Tier 3 source scores `0.38`.
The same signal from Moneycontrol scores `0.855`. That's the difference.

---

## 🛡️ Production Design Decisions

| Decision | Why |
|---|---|
| Scheduler decoupled from API | Users never wait for FinBERT — ingestion runs in background |
| Batch FinBERT inference | 10x faster than one-at-a-time; prevents scheduler job pile-up |
| 60s in-memory cache per ticker | Handles concurrent user spikes without hammering the database |
| `CREATE TABLE IF NOT EXISTS` | Safe restarts — never loses data on redeploy |
| `.env` for API keys | Keys never hit GitHub |

---

## 🎯 Target Use Case

Built specifically for **StockGro / Stoxo** — their own research shows 90% of users lose conviction before acting due to scattered, unverified news. This system provides the structured, credibility-weighted conviction signal layer that Stoxo needs under the hood.

Applicable to: Tickertape, Sensibull, Smallcase, and any Indian fintech platform serving retail investors.

---

## 🗺️ Roadmap

- [x] FinBERT sentiment pipeline
- [x] Source credibility weighting
- [x] FastAPI REST endpoints
- [x] In-memory caching
- [x] APScheduler background ingestion
- [ ] Conviction score aggregation (average weighted_score per ticker)
- [ ] "Priced in?" indicator (compare signal timestamp vs price movement)
- [ ] Signal freshness / decay display
- [ ] Frontend dashboard (React)
- [ ] Docker deployment
- [ ] Render / Railway cloud deploy

---

## 👨‍💻 Built By

**Kiren S** — AI Engineer  
[Portfolio](https://kirenportfolio.netlify.app) · [GitHub](https://github.com/KIREN2612) · [LinkedIn](https://linkedin.com/in/kiren-s-178021322)

> Final-year B.E. AI & Data Science, UIT Coimbatore · Open to AI Engineer roles · 7+ LPA target