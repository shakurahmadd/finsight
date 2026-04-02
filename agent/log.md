# FinSight Agent — Project Log

## 2026-04-02

### What I did
- Started Phase 2: LangGraph agent
- Designed AgentState TypedDict in agent/graph.py with fields: ticker, news, stock_data, sentiment, summary
- Created agent/tools.py with three tool functions
- Built get_news: calls NewsAPI via newsapi-python client, returns 10 articles from last 7 days sorted by publishedAt
- Built get_stock_data: calls yfinance, returns dict with history DataFrame (Close, High, Low, Volume, Dividends) and fundamentals (marketCap, trailingPE, sector, longName)
- Built analyze_sentiment: loads DistilBERT+LoRA from HuggingFace Hub, tokenizes article titles, runs inference, returns list of {title, label} dicts

### Decisions made
- Fixed graph with deterministic node order (not ReAct agent) — flow is always get_news → get_stock_data → analyze_sentiment → LLM summary
- State defined as TypedDict — shared notepad passed between all nodes
- Model loaded once at top of tools.py (not inside function) — avoids repeated weight loading on EC2 t2.micro
- NewsAPI client initialised inside get_news — lightweight, no performance concern
- Used article title (not content) for sentiment — model trained on short headlines, content is truncated by NewsAPI
- Dynamic padding (padding=True) for inference batch — more efficient than max_length padding
- Label mapping: 0=Bearish, 1=Bullish, 2=Neutral (verified against dataset card, not negative/positive/neutral as in CLAUDE.md)
- Date range aligned between news and stock data: both use last 7 days
- yfinance fundamentals accessed via ticker.info (current snapshot, not historical)

### Blockers / questions
- Next: build graph.py nodes and connect them in LangGraph, then add Groq LLM for summary node
