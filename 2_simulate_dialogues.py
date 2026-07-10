import os
import sys
from vertexai import Client, types
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

gcp_project = os.environ.get("GCP_PROJECT", "ninghai-ccai")
gcp_location = os.environ.get("GCP_LOCATION", "us-central1")

try:
    scenarios_file = os.path.join("output", "generated_scenarios.json")
    if not os.path.exists(scenarios_file):
        raise FileNotFoundError(f"Could not find '{scenarios_file}'. Please run 1_generate_scenarios.py first.")
        
    print(f"1. Loading scenarios from {scenarios_file}...")
    with open(scenarios_file, "r") as f:
        eval_dataset = types.EvaluationDataset.model_validate_json(f.read())
        
    print("\n2. Initializing Vertex AI Client...")
    client = Client(project=gcp_project, location=gcp_location)
    
    print("\n3. Importing Travel Agent...")
    from travel_agent import agent
    
    print("\n4. Running programmatic multi-turn user simulation (run_inference)...")
    eval_dataset_with_traces = client.evals.run_inference(
        agent=agent,
        src=eval_dataset,
        config={
            "allow_cross_region_model": True,
            "user_simulator_config": {
                "model_name": "gemini-3.5-flash",
                "max_turn": 5
            }
        }
    )
    
    os.makedirs("output", exist_ok=True)
    output_file = os.path.join("output", "simulated_traces.json")
    print(f"\n5. Persisting simulation traces to {output_file}...")
    if eval_dataset_with_traces.eval_dataset_df is not None:
        import json
        import datetime
        import base64
        def json_default(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            if isinstance(obj, bytes):
                return base64.b64encode(obj).decode("utf-8")
            raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")
            
        df_dict = eval_dataset_with_traces.eval_dataset_df.to_dict(orient="records")
        with open(output_file, "w") as f:
            json.dump(df_dict, f, indent=2, ensure_ascii=False, default=json_default)
    else:
        print("Warning: eval_dataset_df is None. Saving empty file.")
        with open(output_file, "w") as f:
            f.write("[]")
        
    print("\n=== Simulation Completed Successfully! ===")
    print(f"Traces for {len(eval_dataset_with_traces.eval_dataset_df) if eval_dataset_with_traces.eval_dataset_df is not None else 0} cases saved.")

except Exception as e:
    print("\nError during simulation run:", e, file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
