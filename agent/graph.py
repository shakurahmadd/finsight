from agent.tools import get_news, get_stock_data, analyze_sentiment, get_sec_filings
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
import ast
import json
from db.database import SessionLocal
from db.models import DkKnowledge, SectorMacroMapping, MacroIndicator

load_dotenv()

groq_key = os.getenv("GROQ_API")
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key)

tools = [get_news, get_stock_data, analyze_sentiment, get_sec_filings]

llm_with_tools = llm.bind_tools(tools)

session = SessionLocal()

def agent_node(state):
    messages = state['messages']
    sector = None
    for message in messages:
        if isinstance(message, ToolMessage) and "sector" in message.content:
            message_to_dict = json.loads(message.content)
            sector = message_to_dict['fundamentals']['sector']
            break
    if sector:
        sector_benchmarks = session.query(DkKnowledge).filter(DkKnowledge.sector == sector).all()
        macro_mappings = session.query(SectorMacroMapping).filter(SectorMacroMapping.sector == sector).all()

        indicator_ids = [m.indicator_id for m in macro_mappings]
        macro_indicators = session.query(MacroIndicator).filter(MacroIndicator.id.in_(indicator_ids)).all()

        # system prompt string
        prompt = f"You are a financial research analyst. Use the following domain knowledge to ground your reasoning:\n\nSector Benchmarks ({sector}):\n"

        # append sector benchmarks
        for b in sector_benchmarks:
            prompt += f"- {b.metric_name}: avg={b.sector_avg}, upper={b.upper_threshold}, lower={b.lower_threshold}\n"

        # append macro indicators
        prompt += f"\nMacro Indicators:\n"
        for m in macro_indicators:
            prompt += f"- {m.indicator_name}: {m.current_value} (change: {m.change})\n"
        
        messages = [SystemMessage(content=prompt)] + messages
        
    response = llm_with_tools.invoke(messages)
    return {'messages' : response}



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