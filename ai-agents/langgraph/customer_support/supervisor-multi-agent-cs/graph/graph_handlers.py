from typing import Callable

from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START

from state.common_state import State
from utilities.exception_handlers import handle_tool_error
from tools.user_info.fetch_user_flight_information import fetch_user_flight_information

def user_info(state: State):
    return {"user_info": fetch_user_flight_information.invoke({})}

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node

def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )
    
# This node will be shared for exiting all specialized assistants
def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }

def common_graph_builder(builder: StateGraph) -> StateGraph:
    builder.add_node("fetch_user_info", user_info)
    builder.add_edge(START, "fetch_user_info")
    
    builder.add_node("leave_skill", pop_dialog_state)
    builder.add_edge("leave_skill", "primary_assistant")
    return builder
    

