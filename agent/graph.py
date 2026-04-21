from agent.tools import get_news, get_stock_data, analyze_sentiment, retrieve_rag_chunks
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
import json
from db.database import SessionLocal
from db.models import DkKnowledge, SectorMacroMapping, MacroIndicator


load_dotenv()

groq_key = os.getenv("GROQ_API")
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_key)

tools = [get_news, get_stock_data, analyze_sentiment, retrieve_rag_chunks]

llm_with_tools = llm.bind_tools(tools)

BASE_SYSTEM_PROMPT = """You are a senior equity research analyst writing for sophisticated retail investors.

You have access to the following tools: get_news, analyze_sentiment, get_stock_data, and retrieve_rag_chunks. You decide which tools to call, in what order, and how many times — but every factual claim in the report must trace back to a tool result. If you cannot ground a claim with a tool call, do not make it.

Before writing the report, use get_stock_data to identify the ticker's sector, then apply the relevant sector baselines when interpreting fundamentals. You are expected to reason about what each tool result tells you and decide whether further calls are needed — for example, if sentiment is anomalous, investigate further before concluding.

If a tool returns no data or an error, write: "Data unavailable — [tool name] returned no results." Never infer, estimate, or substitute values from training knowledge.

---

## Verdict
One sentence: overall assessment of the stock right now (bullish, bearish, or neutral) and why.

## Sentiment Signal
What the recent news is saying. Is sentiment bullish, bearish, or neutral? Is it shifting? Cite the confidence level and the source signal directly.

## Earnings
Latest EPS actual vs estimate. Surprise percentage. Is there a pattern of beating or missing? What does this suggest about management guidance credibility?

## SEC Filings
Anything notable from recent filings. Highlight material 8-K events (CEO departure, restatement, acquisition). Call out significant insider buying or selling from Form 4. If nothing notable, say so briefly.

## Key Risks
The most important risks from the 10-K risk factors section. Be specific — not generic boilerplate. Flag anything unusual as a **RED FLAG**.

## Fundamentals
PE ratio, market cap, sector. Interpret the numbers in context — not just raw values. Compare to sector norms where possible. State the sector explicitly.

---

## Style Rules
- Cite specific numbers from tool results — never fabricate them
- If a signal is anomalous, label it **RED FLAG** in bold
- Be concise and direct — no filler phrases
- Do not describe which tools you called — report findings only
- Every number in the report must trace back to a tool result
"""


def agent_node(state):
    messages = state['messages']
    sector = None
    for message in messages:
        if isinstance(message, ToolMessage) and "sector" in message.content:
            try:
                message_to_dict = json.loads(message.content)
                sector = message_to_dict['fundamentals']['sector']
            except (json.JSONDecodeError, KeyError):
                pass
            break

    system_prompt = BASE_SYSTEM_PROMPT

    if sector:
        session = SessionLocal()
        try:
            sector_benchmarks = session.query(DkKnowledge).filter(DkKnowledge.sector == sector).all()
            macro_mappings = session.query(SectorMacroMapping).filter(SectorMacroMapping.sector == sector).all()
            indicator_ids = [m.indicator_id for m in macro_mappings]
            macro_indicators = session.query(MacroIndicator).filter(MacroIndicator.id.in_(indicator_ids)).all()

            if sector_benchmarks:
                system_prompt += f"\n\nSector Benchmarks ({sector}):\n"
                for b in sector_benchmarks:
                    system_prompt += f"- {b.metric_name}: avg={b.sector_avg}, upper={b.upper_threshold}, lower={b.lower_threshold}\n"

            if macro_indicators:
                system_prompt += f"\nMacro Indicators:\n"
                for m in macro_indicators:
                    system_prompt += f"- {m.indicator_name}: {m.current_value} (change: {m.change})\n"
        finally:
            session.close()

    messages = [SystemMessage(content=system_prompt)] + messages
    response = llm_with_tools.invoke(messages)
    return {'messages': response}



graph = StateGraph(MessagesState)

graph.add_node("agent", agent_node)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("agent")

# condition edge from the agent node
graph.add_conditional_edges("agent", tools_condition)

graph.add_edge("tools", "agent")
# compile graph
graph_app = graph.compile()

if __name__ == "__main__":
    result = graph_app.invoke({"messages" : [HumanMessage(content="Analyse: AAPL")]})
    print(result['messages'][-1].content)