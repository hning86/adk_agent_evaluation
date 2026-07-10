import os
import sys
from google.adk import Agent
from vertexai import Client, types

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

gcp_project = os.environ.get("GCP_PROJECT", "ninghai-ccai")
gcp_location = os.environ.get("GCP_LOCATION", "us-central1")

from google.adk.models.google_llm import Gemini
from google.genai import Client as GenaiClient

# Define our mock tools
def find_flights(origin: str, destination: str, date: str) -> str:
    """Find available flights between origin and destination on a given date.
    
    Args:
        origin: The starting airport code or city (e.g., 'SFO').
        destination: The destination airport code or city (e.g., 'JFK').
        date: The date of the flight (e.g., '2026-07-13').
        
    Returns:
        A list of available flights with IDs and prices.
    """
    print(f"[Tool: find_flights] Called with origin={origin}, destination={destination}, date={date}")
    # Handle SFO to JFK
    if origin == "SFO" and destination in ["JFK", "New York"]:
        return "Available flights: Flight ID FL-102 (Price: $350, Time: 08:00 AM), Flight ID FL-205 (Price: $420, Time: 01:00 PM)"
    # Handle SFO to CDG (Paris)
    elif origin == "SFO" and destination in ["CDG", "Paris", "France"]:
        return "Available flights: Flight ID FL-901 (Price: $850, Time: 04:00 PM), Flight ID FL-902 (Price: $950, Time: 09:30 PM)"
    # Handle Cleveland SFO-CLE
    elif origin == "SFO" and destination in ["CLE", "Cleveland"]:
        return "Available flights: Flight ID FL-501 (Price: $310, Time: 10:00 AM), Flight ID FL-502 (Price: $380, Time: 03:00 PM)"
    else:
        return f"No direct flights found from {origin} to {destination} on {date}. Try SFO to CDG, SFO to CLE, or SFO to JFK."

def book_flight(flight_id: str) -> str:
    """Book a flight using its flight ID.
    
    Args:
        flight_id: The unique ID of the flight to book.
        
    Returns:
        A confirmation message with a booking reference code.
    """
    print(f"[Tool: book_flight] Called with flight_id={flight_id}")
    valid_ids = ["FL-102", "FL-205", "FL-501", "FL-502", "FL-901", "FL-902"]
    if flight_id in valid_ids:
        ref_code = (hash(flight_id) % 9000) + 1000
        return f"Successfully booked flight {flight_id}! Booking confirmation reference: BK-{ref_code}."
    else:
        return f"Failed to book flight {flight_id}. Invalid flight ID. Please pick from available flights."


def format_simulation_trace(agent_data) -> str:
    """Formats the raw agent_data trace from evaluation results for human readability."""
    if not agent_data:
        return "  No trace data available."
        
    if isinstance(agent_data, str):
        try:
            import json
            agent_data = json.loads(agent_data)
        except Exception:
            try:
                import ast
                agent_data = ast.literal_eval(agent_data)
            except Exception:
                return f"  [Raw agent_data]: {agent_data}"

    if not isinstance(agent_data, dict):
        return f"  [Raw agent_data]: {agent_data}"

    output = []
    turns = agent_data.get("turns", [])
    for turn in turns:
        turn_idx = turn.get("turn_index", 0)
        output.append(f"\n  --- Turn {turn_idx + 1} ---")
        
        events = turn.get("events", [])
        for event in events:
            author = event.get("author", "unknown")
            content = event.get("content", {})
            parts = content.get("parts", [])
            
            for part in parts:
                if "text" in part:
                    text_content = part["text"].strip()
                    # Indent multi-line text for clean reading
                    indented = "\n".join(f"      {line}" for line in text_content.split("\n"))
                    output.append(f"    * {author.upper()}:\n{indented}")
                elif "function_call" in part:
                    fcall = part["function_call"]
                    name = fcall.get("name")
                    args = fcall.get("args")
                    output.append(f"    * {author.upper()} (Tool Call): {name}({args})")
                elif "function_response" in part:
                    fresp = part["function_response"]
                    name = fresp.get("name")
                    response = fresp.get("response")
                    output.append(f"    * {author.upper()} (Tool Response): {name} -> {response}")
    return "\n".join(output)


try:
    print("1. Initializing Vertex AI Client...")
    client = Client(project=gcp_project, location=gcp_location)
    
    print("\n2. Defining Travel Agent using google.adk.Agent...")    
    travel_agent = Agent(
        model="gemini-3.5-flash",
        name='travel_agent',
        instruction='You are a travel expert, help users to find flights, book flights with flight ID',
        tools=[find_flights, book_flight],
    )
    
    print("\n3. Loading AgentInfo representation...")
    travel_agent_info = types.evals.AgentInfo.load_from_agent(agent=travel_agent)
    
    print("\n4. Generating 5 conversation scenarios...")
    eval_dataset = client.evals.generate_conversation_scenarios(
        agent_info=travel_agent_info,
        allow_cross_region_model=True,
        config={
            "count": 5,
            "generation_instruction": "Generate scenarios where the user tries to book a flight SFO to JFK, and pivots on date or time.",
            "environment_context": "Today is Monday. I am located in San Francisco. Flights to Paris, New York, Cleveland, Tokyo, Chicago, Sydney, etc are available.",
        },
    )
    
    # Let's print the first generated scenario
    case = eval_dataset.eval_cases[0]
    print("\n=== 1st Generated Scenario ===")
    print("Title:", case.user_scenario.test_case_title)
    print("Starting Prompt:", case.user_scenario.starting_prompt)
    print("Conversation Plan:", case.user_scenario.conversation_plan)
    
    print("\n5. Running programmatic multi-turn simulation (run_inference)...")
    eval_dataset_with_traces = client.evals.run_inference(
        agent=travel_agent,
        src=eval_dataset,
        config={
            "allow_cross_region_model": True,
            "user_simulator_config": {
                "model_name": "gemini-3.5-flash",
                "max_turn": 5
            }
        }
    )
    
    print("\n6. Simulation Completed! Processing results...")
    print("Dataset traces schema:", type(eval_dataset_with_traces))
    
    # Print traces
    if getattr(eval_dataset_with_traces, "eval_cases", None) is not None:
        for idx, eval_case in enumerate(eval_dataset_with_traces.eval_cases):
            print(f"\n=================== TRACE {idx+1} ===================")
            scenario = eval_case.user_scenario
            print("Title:", scenario.test_case_title)
            print("Starting Prompt:", scenario.starting_prompt)
            print("Conversation Plan:", scenario.conversation_plan)
            
            # Print the actual turns
            print("\n--- Dialogue Transcript ---")
            turns = getattr(eval_case, "turns", [])
            if turns:
                for turn_idx, turn in enumerate(turns):
                    print(f"Turn {turn_idx+1}:")
                    user_msg = getattr(turn, "user_message", None)
                    agent_msg = getattr(turn, "agent_message", None)
                    print(f"  User: {user_msg}")
                    print(f"  Agent: {agent_msg}")
            else:
                print("Trace keys:", eval_case.model_fields.keys())
                print(eval_case)
    else:
        print("\nNo eval_cases in the result. Checking eval_dataset_df...")
        df = getattr(eval_dataset_with_traces, "eval_dataset_df", None)
        if df is not None:
            print(f"DataFrame loaded! Columns: {list(df.columns)}")
            print("\n--- Dialogue Transcript from DataFrame ---")
            for idx, row in df.iterrows():
                print(f"\n=================== SIMULATION CASE {idx+1} ===================")
                for col in df.columns:
                    val = row[col]
                    if col == 'agent_data':
                        print("  agent_data (Simulation Trace):")
                        print(format_simulation_trace(val))
                    elif isinstance(val, list):
                        print(f"  {col}:")
                        for item in val:
                            print(f"    - {item}")
                    else:
                        print(f"  {col}: {val}")
        else:
            print("No eval_cases or eval_dataset_df available in results.")
            print("Available attributes:", [a for a in dir(eval_dataset_with_traces) if not a.startswith('_')])

except Exception as e:
    print("\nError during run_inference:", e, file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
