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
    traces_file = os.path.join("output", "simulated_traces.json")
    
    if not os.path.exists(scenarios_file) or not os.path.exists(traces_file):
        raise FileNotFoundError("Please make sure you have run both 1_generate_scenarios.py and 2_simulate_dialogues.py first.")
        
    print(f"1. Loading original scenarios from {scenarios_file}...")
    with open(scenarios_file, "r") as f:
        eval_dataset = types.EvaluationDataset.model_validate_json(f.read())
        
    print(f"2. Loading simulation traces from {traces_file}...")
    import pandas as pd
    df_traces = pd.read_json(traces_file)
    # Wrap in EvaluationDataset so the model fields are properly configured for the ADK evaluate call
    eval_dataset_with_traces = types.EvaluationDataset(eval_dataset_df=df_traces)
        
    print("\n3. Initializing Vertex AI Client...")
    client = Client(project=gcp_project, location=gcp_location)
    
    print("\n4. Running Evals Evaluate...")
    # Evaluate with multi_turn_task_success_v1, multi_turn_trajectory_quality_v1, and multi_turn_tool_use_quality_v1
    eval_result = client.evals.evaluate(
        dataset=eval_dataset_with_traces,
        metrics=[
            types.Metric(name="multi_turn_task_success_v1"),
            types.Metric(name="multi_turn_trajectory_quality_v1"),
            types.Metric(name="multi_turn_tool_use_quality_v1")
        ],
        allow_cross_region_model=True,
    )
    
    print("\n=== Evaluation Completed! ===")
    print("Aggregated Results:")
    if eval_result.summary_metrics:
        for metric_result in eval_result.summary_metrics:
            print(f"  Metric Name: {metric_result.metric_name}")
            print(f"    Mean Score: {metric_result.mean_score}")
            print(f"    Pass Rate: {metric_result.pass_rate}")
            print(f"    Total Cases: {metric_result.num_cases_total}")
            print(f"    Valid Cases: {metric_result.num_cases_valid}")
            print(f"    Error Cases: {metric_result.num_cases_error}")
    else:
        print("  No summary metrics returned.")
        
    print("\nDetailed Results:")
    eval_cases = eval_dataset.eval_cases if eval_dataset and getattr(eval_dataset, "eval_cases", None) else []
    if eval_result.eval_case_results:
        for idx, case_res in enumerate(eval_result.eval_case_results):
            title = "Unnamed Case"
            plan = "No plan available"
            if idx < len(eval_cases):
                scenario = eval_cases[idx].user_scenario
                title = scenario.test_case_title
                plan = scenario.conversation_plan
                
            print(f"\nCase {idx+1}: {title}")
            print(f"  Conversation Plan: {plan}")
            
            if case_res.response_candidate_results:
                for cand_res in case_res.response_candidate_results:
                    if cand_res.metric_results:
                        for metric_name, metric_res in cand_res.metric_results.items():
                            print(f"  - Metric Name: {metric_name}")
                            print(f"    Score: {metric_res.score}")
                            print(f"    Explanation: {metric_res.explanation}")
                            if metric_res.error_message:
                                print(f"    Error: {metric_res.error_message}")
    else:
        print("  No detailed case results returned.")

    # Persist the evaluation results to file
    os.makedirs("output", exist_ok=True)
    output_file = os.path.join("output", "evaluation_report.json")
    print(f"\n5. Persisting evaluation results to {output_file}...")
    if eval_result.evaluation_dataset:
        for ds in eval_result.evaluation_dataset:
            ds.eval_dataset_df = None
    with open(output_file, "w") as f:
        f.write(eval_result.model_dump_json(indent=2))

except Exception as e:
    print("\nError during evaluation:", e, file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)
