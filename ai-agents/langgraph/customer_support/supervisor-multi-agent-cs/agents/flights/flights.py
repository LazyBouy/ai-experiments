from langchain_core.pydantic_v1 import BaseModel, Field

from agents.common_classes import Assistant
from runnable_handlers import update_flight_runnable, update_flight_sensitive_tools, update_flight_safe_tools, update_flight_tools

# Primary Assistant
class ToFlightBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle flight updates and cancellations."""

    request: str = Field(
        description="Any necessary followup questions the update flight assistant should clarify before proceeding."
    )
    
flight_assistant = Assistant(update_flight_runnable)

flight_assistant_sensitive_tools = update_flight_sensitive_tools
flight_assistant_safe_tools = update_flight_safe_tools
flight_assistant_safe_tools = update_flight_tools