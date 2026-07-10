import os
import sys
from vertexai import Client, types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

gcp_project = os.environ.get("GCP_PROJECT", "ninghai-ccai")
gcp_location = os.environ.get("GCP_LOCATION", "us-central1")

try:
    print("1. Initializing Vertex AI Client...")
    client = Client(project=gcp_project, location=gcp_location)
    
    print("\n2. Importing Travel Agent to extract AgentInfo...")
    from travel_agent import agent
    
    print("\n3. Loading AgentInfo representation...")
    travel_agent_info = types.evals.AgentInfo.load_from_agent(agent=agent)
    
    print("\n4. Generating conversation scenarios...")
    eval_dataset = client.evals.generate_conversation_scenarios(
        agent_info=travel_agent_info,
        allow_cross_region_model=True,
        config={
            "count": 3,
            "generation_instruction": "Generate scenarios where the user tries to book a flight SFO to JFK, and pivots on date or time.",
            "environment_context": "Today is Monday. I am located in San Francisco. Flights to Paris, New York, Cleveland, Tokyo, Chicago, Sydney, etc are available.",
        },
    )
    
    os.makedirs("output", exist_ok=True)
    output_file = os.path.join("output", "generated_scenarios.json")
    print(f"\n5. Persisting generated scenarios to {output_file}...")
    eval_dataset.eval_dataset_df = None
    with open(output_file, "w") as f:
        f.write(eval_dataset.model_dump_json(indent=2))
        
    print("\n=== Scenario Generation Completed Successfully! ===")
    print(f"Generated {len(eval_dataset.eval_cases)} scenarios.")
    for idx, case in enumerate(eval_dataset.eval_cases):
        print(f"\n  Scenario {idx+1}: {case.user_scenario.test_case_title}")
        print(f"    Plan: {case.user_scenario.conversation_plan}")

except Exception as e:
    print("\nError during scenario generation:", e, file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
