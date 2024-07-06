# Customer Support - Travel Agency - Supervisor-Multiagent-Model

from langgraph.graph import StateGraph

from state.common_state import State
from graph_handlers import common_graph_builder
from flights.graph_handlers import flight_agent_node, flight_agent_edge

builder = StateGraph(State)

# Common: Nodes & Edges
common_graph_builder(builder=builder)

# Flights: Nodes & Edges
flight_agent_node(builder=builder)
flight_agent_edge(builder=builder)



