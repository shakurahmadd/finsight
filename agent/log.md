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

### What I did (continued)
- Added __init__.py to agent/ and tests/ to make them importable packages
- Wrote tests/test_tools.py with tests for all three tools
- test_get_news: asserts list of dicts, length 10, title key present
- test_stock_data: asserts dict with history (DataFrame) and fundamentals (dict) keys, marketCap present
- test_analyze_sentiment: uses fake articles list, asserts list of dicts with label key
- All 3 tests passing

### What I did (continued)
- Built graph.py with four nodes: get_news_node, get_stock_data_node, analyze_sentiment_node, generate_summary_node
- Connected nodes with fixed edges in LangGraph: get_news → get_stock_data → analyze_sentiment → generate_summary
- Used StateGraph(AgentState) with set_entry_point and compile()
- Added Groq LLM (llama-3.1-8b-instant) loaded once at top of graph.py
- generate_summary_node builds an f-string prompt with ticker, articles, stock_data, sentiment and calls llm.invoke()
- Tested end-to-end with app.invoke({"ticker": "AAPL"}) — produced a full research summary successfully

### Decisions made (continued)
- Groq ChatGroq model loaded once at module level — same reasoning as sentiment model
- Nodes follow pattern: read from state → call tool → return updated fields dict
- if __name__ == "__main__" guard used for manual testing — prevents graph execution on import
- prompt uses f-string with triple quotes for multiline formatting

### Blockers / questions
- Phase 2 complete — next is Phase 3: FastAPI endpoints + PostgreSQL schema
