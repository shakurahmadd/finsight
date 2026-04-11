from agent.tools import get_news, get_stock_data, analyze_sentiment, get_sec_filings
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import HumanMessage


load_dotenv()

groq_key = os.getenv("GROQ_API")
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key)

tools = [get_news, get_stock_data, analyze_sentiment, get_sec_filings]

llm_with_tools = llm.bind_tools(tools)

def agent_node(state):
    messages = state['messages']
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