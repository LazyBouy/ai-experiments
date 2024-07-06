import tools.flights as tools

from llms.groq import groq_llm as llm
from agents.common_classes import CompleteOrEscalate
from prompts.flights.flight_booking import flight_booking_prompt

update_flight_safe_tools = [tools.search_flights]
update_flight_sensitive_tools = [tools.update_ticket_to_new_flight, tools.cancel_ticket]
update_flight_tools = update_flight_safe_tools + update_flight_sensitive_tools

update_flight_runnable = flight_booking_prompt | llm.bind_tools(
    update_flight_tools + [CompleteOrEscalate]
)





