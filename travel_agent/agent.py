from google.adk import Agent
from .tools import find_flights, book_flight

travel_agent = Agent(
    model="gemini-3.5-flash",
    name='travel_agent',
    instruction='You are a travel expert, help users to find flights, book flights with flight ID',
    tools=[find_flights, book_flight],
)

# Export the agent using standard ADK variable conventions
agent = travel_agent
root_agent = travel_agent
