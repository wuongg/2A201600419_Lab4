from email import message
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from tools import (
    search_flights,
    search_hotels,
    calculate_budget,
    get_attractions,
    build_itinerary,
    estimate_daily_cost,
    normalize_city_name,
    get_supported_cities,
    get_supported_routes,
    recommend_flight,
    recommend_hotel,
    estimate_trip_cost,
    plan_trip,
)
from dotenv import load_dotenv
import sys

load_dotenv()

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
tools_list = [
    search_flights,
    search_hotels,
    calculate_budget,
    get_attractions,
    build_itinerary,
    estimate_daily_cost,
    normalize_city_name,
    get_supported_cities,
    get_supported_routes,
    recommend_flight,
    recommend_hotel,
    estimate_trip_cost,
    plan_trip,
]
llm = ChatOpenAI(model="gpt-4o-mini")
llm_with_tools = llm.bind_tools(tools_list)

def agent_node(state: AgentState):
    messages = state["messages"]
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)

    if response.tool_calls:
        for tc in response.tool_calls:
            print(f"Calling tool: {tc['name']} ({tc['args']})")
    else:
        print("Direct answer (no tools)")
    return {"messages": [response]}

builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)

tool_node = ToolNode(tools_list)
builder.add_node("tools", tool_node)

builder.add_edge(START, "agent")

builder.add_conditional_edges("agent", tools_condition)

builder.add_edge("tools", "agent")

builder.add_edge("agent", END)

graph = builder.compile()

# 6. Chat loop
if __name__ == "__main__":
    # Force UTF-8 for Windows consoles to avoid Unicode errors
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass

    print("=" * 60)
    print("TravelBuddy - Smart Travel Assistant")
    print("  Type 'quit' to exit")
    print("=" * 60)

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break

        print("\nTravelBuddy is thinking...")
        result = graph.invoke({"messages": [("human", user_input)]})
        final = result["messages"][-1]
        print(f"\nTravelBuddy: {final.content}")