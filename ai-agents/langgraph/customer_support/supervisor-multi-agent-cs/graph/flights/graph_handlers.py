import agents.flights.flights as flights
import agents.common_classes as cc

from typing import Literal
from langgraph.prebuilt import tools_condition
from langgraph.graph import StateGraph, END

from graph_handlers import create_entry_node, create_tool_node_with_fallback
from state.common_state import State

def route_update_flight(
    state: State,
) -> Literal[
    "update_flight_sensitive_tools",
    "update_flight_safe_tools",
    "leave_skill",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == cc.CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in flights.flight_assistant_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "update_flight_safe_tools"
    return "update_flight_sensitive_tools"

agent_entry_node = create_entry_node("Flight Updates & Booking Assistant", "update_flight")

agent_main = flights.flight_assistant

agent_sensitive_tools_fallback = create_tool_node_with_fallback(flights.flight_assistant_sensitive_tools)
agent_safe_tools_fallback = create_tool_node_with_fallback(flights.flight_assistant_safe_tools)

def flight_agent_node(builder: StateGraph) -> StateGraph:
    
    builder.add_node(
        "enter_update_flight",
        agent_entry_node,
    )
    
    builder.add_node(
        "update_flight",
        agent_main
    )
    
    builder.add_node(
        "update_flight_sensitive_tools",
        agent_sensitive_tools_fallback
    )
    
    builder.add_node(
        "update_flight_safe_tools",
        agent_safe_tools_fallback
    )
    
    return builder
    
def flight_agent_edge(builder: StateGraph) -> StateGraph:
    builder.add_edge(
        "update_flight_sensitive_tools", 
        "update_flight"
    )
    
    builder.add_edge(
        "update_flight_safe_tools",
        "update_flight"
    )
    
    builder.add_conditional_edges(
        "update_flight",
        route_update_flight
    )
    
    return builder