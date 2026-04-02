# FinSight Agent — Reference Notes

## LangGraph

### Key concepts
- **Graph**: nodes connected by edges, state flows through the graph
- **State**: TypedDict shared between all nodes — each node reads from and writes to it
- **Nodes**: Python functions that take state and return updated state
- **Edges**: define the order nodes execute (fixed edges = deterministic pipeline)
- **Fixed vs ReAct**: FinSight uses fixed edges (deterministic order) not a ReAct agent (LLM decides order) — appropriate when the workflow is always the same

### AgentState fields
- `ticker: str` — input stock ticker
- `news: list[dict]` — articles from NewsAPI
- `stock_data: dict` — history DataFrame + fundamentals dict from yfinance
- `sentiment: list[dict]` — title/label pairs from DistilBERT
- `summary: str` — final research summary from LLM

## Tools

### get_news
- Uses newsapi-python client library
- Endpoint: get_everything (not top_headlines — broader coverage for sentiment)
- Parameters: q=ticker, language='en', from_param=7 days ago, sort_by='publishedAt', page_size=10
- Returns: list[dict] — raw article objects from NewsAPI

### get_stock_data
- Uses yfinance Ticker object
- history(): returns DataFrame with OHLCV + Dividends for date range
- Dropped columns: Open, Stock Splits (not useful for sentiment-based summary)
- info: current snapshot dict — extract marketCap, trailingPE, sector, longName
- Returns: dict with 'history' (DataFrame) and 'fundamentals' (dict)

### analyze_sentiment
- Model loaded once at module level (not per call) — avoids repeated weight loading
- Loading pattern: base model (AutoModelForSequenceClassification) → LoRA adapters (PeftModel.from_pretrained) → tokenizer
- Inference: tokenize titles with dynamic padding, run in eval() + torch.no_grad()
- Label mapping: 0=Bearish, 1=Bullish, 2=Neutral
- Returns: list[dict] with 'title' and 'label' keys

## Graph structure

### Building the graph
```python
graph = StateGraph(AgentState)
graph.add_node("name", function_reference)  # no () on function
graph.set_entry_point("first_node")
graph.add_edge("from_node", "to_node")
app = graph.compile()
```

### Running the graph
```python
result = app.invoke({"ticker": "AAPL"})  # initial state
result['summary']  # access final state fields
```

### Node pattern
```python
def some_node(state):
    value = state['field']       # read from state
    result = do_something(value) # do work
    return {'field': result}     # return updated fields only
```

### LLM integration
- ChatGroq loaded once at module level with model="llama-3.1-8b-instant"
- Called via llm.invoke(prompt_string)
- Response text accessed via response.content

## Environment / secrets
- API keys stored in .env, loaded with python-dotenv
- Never hardcode keys or paste them in chat
- load_dotenv() called once at top of tools.py
