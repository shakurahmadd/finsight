# FinSight

An autonomous financial research agent for retail investors. Given a stock ticker, FinSight retrieves and analyses data from multiple sources, generates a structured research report with red flag alerts, and tracks sentiment momentum across a watchlist.

---

## Architecture

FinSight is built around a **LangGraph ReAct agent** — the LLM sits at the centre, decides which tools to call and in what order, and loops until it has enough signal to produce a final answer. This is a deliberate departure from V1's fixed linear pipeline.

```mermaid
graph TD
    A[User Query - Ticker] --> B[Agent Node - LLM]
    B -->|tool call| D[get_news]
    B -->|tool call| E[analyze_sentiment]
    B -->|tool call| F[get_stock_data]
    B -->|tool call| G[get_earnings]
    B -->|tool call| H[retrieve_rag_chunks]
    D -->|result| B
    E -->|result| B
    F -->|result| B
    G -->|result| B
    H -->|result| B
    B -->|all data gathered| I[Structured Research Report]
```

**Key architectural decisions:**

- **ReAct over linear pipeline** — tools aren't always needed in the same order or combination. The LLM reasons about what signal it already has and decides whether additional calls are justified.
- **RAG for SEC filings** — full 10-K and 8-K documents are chunked, embedded with `all-MiniLM-L6-v2`, and stored in PostgreSQL via pgvector. At query time, the most relevant chunks are retrieved via cosine similarity. Replaces naive 300-character truncation.
- **DK-CoT (Domain Knowledge Chain-of-Thought)** — sector benchmarks and FRED macro indicators are injected into the agent prompt before reasoning, grounding the LLM in real financial context rather than general knowledge.
- **Fine-tuned DistilBERT** — trained on `zeroshot/twitter-financial-news-sentiment` with LoRA/PEFT. Used for per-article sentiment scoring and nightly weighted sentiment aggregation across the watchlist.
- **Nightly batch jobs** — NewsAPI allows 100 requests/day. All 23 watchlisted tickers are pre-fetched at 1am, scored, and cached. Daytime requests always hit cache.
- **pgvector over FAISS** — keeps all embeddings in the same PostgreSQL database. No separate vector store to manage or synchronise.

---

## Features

### Research Agent
- Structured research report: Verdict, Sentiment Signal, Earnings, SEC Filings, Key Risks, Fundamentals
- All data grounded in real tool calls — no hallucinated numbers
- Red flag detection for anomalous signals
- Sector benchmarks and macro context injected via DK-CoT

### Sentiment Pipeline
- Fine-tuned DistilBERT (LoRA) for financial news sentiment (Bullish / Bearish / Neutral)
- Weighted sentiment score: recency decay × model confidence
- 30-day sentiment history tracked per ticker

### SEC Filing RAG
- Full 10-K (MD&A, Risk Factors) and 8-K documents chunked and embedded
- Semantic retrieval via pgvector cosine similarity
- 21 of 23 watchlisted tickers populated (BP and SHEL excluded — no SEC filings)

### Anomaly Detection (data accumulation phase)
- Nightly feature vectors: sentiment score, earnings surprise, insider volume, filing frequency, price volatility
- Isolation Forest training deferred until ~60 days of data accumulated (started April 2026)
- LSTM Autoencoder planned as Phase 2 upgrade

### Portfolio & Watchlist
- JWT-authenticated portfolio CRUD — create/delete portfolios, add/remove holdings
- Weighted sentiment aggregation across portfolio holdings
- Watchlist of 23 major tickers with live sentiment signals

### Frontend
- React + Vite + MUI v9 dark theme 
- Ticker Research Page: research summary, 30-day sentiment chart, news feed, earnings table, SEC filings
- Portfolio Dashboard: portfolio and holdings management
- Watchlist Page: all tickers with Bullish/Bearish/Neutral chips

---

## Tech Stack

| Layer | Technology |
|---|---|
| Agent orchestration | LangGraph (ReAct pattern) |
| LLM | Groq llama-3.3-70b-versatile |
| Sentiment model | Fine-tuned DistilBERT (LoRA/PEFT) via HuggingFace |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 |
| Vector search | pgvector (PostgreSQL extension) |
| API | FastAPI + JWT auth |
| Database | PostgreSQL + Alembic migrations |
| Scheduling | APScheduler (nightly jobs) |
| Frontend | React + Vite + MUI v9 + Recharts |
| Observability | LangSmith |
| Containerisation | Docker + docker-compose |
| CI | GitHub Actions |
| Deployment | AWS EC2 t3.small |
| Data sources | NewsAPI, yfinance, SEC EDGAR, FRED |

---

## Local Setup

**Prerequisites:** Docker, docker-compose, Python 3.9

```bash
git clone https://github.com/shakurahmad/finsight.git
cd finsight
```

Create a `.env` file:
```
DB_URL=postgresql://shakurahmad:postgres@localhost:5433/finsight
NEWS_API=your_newsapi_key
GROQ_API=your_groq_key
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=finsight
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

Start the stack:
```bash
docker-compose up --build
```

The API will be available at `http://localhost:8000/docs`.

To populate SEC filing chunks for a ticker:
```bash
docker exec -it finsight-app-1 python -c "from rag.filing_rag import process_filing; process_filing('AAPL')"
```

---

## Roadmap

- [ ] **Nginx + frontend deployment** — serve React static files via Nginx in docker-compose alongside FastAPI
- [ ] **Sector Comparison page** — heatmap grid of tickers vs signals, sortable by column
- [ ] **Portfolio health score** — weighted sentiment aggregation, concentration risk, per-holding alert feed
- [ ] **Isolation Forest anomaly detection** — train on accumulated feature vectors (~60 days from April 2026)
- [ ] **LSTM Autoencoder** — replace Isolation Forest with temporal anomaly detection once baseline is working
- [ ] **CD pipeline** — automate EC2 deployment on push to main

---

## Research

This project implements ideas from:

- *Leveraging large language model as news sentiment predictor in stock markets: a knowledge-enhanced strategy* — Springer Nature, May 2025 (DK-CoT implementation)
