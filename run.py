# Copyright Sierra

import argparse
import yaml
import os
from tau_bench.types import RunConfig
from tau_bench.run import run
from typing import List, Optional
import json
import os
from datetime import datetime


def parse_args() -> RunConfig:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="The model to use for the agent",
    )
    parser.add_argument(
        "--task-ids", 
        type=int, 
        nargs="+", 
        required=True,
        help="Run only the tasks with the given IDs"
    )
    args = parser.parse_args()
    
    # Load config from yaml file
    config_path = "config.yaml"
    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)
    
    # Override with command line arguments
    config_data["model"] = args.model
    config_data["task_ids"] = args.task_ids
    
    print("Configuration:")
    for key, value in config_data.items():
        print(f"  {key}: {value}")
    
    return RunConfig(**config_data)


def format_results(config: RunConfig, unformatted_results_path: str) -> None:
    """Format the unformatted results according to the MT Benchmark schema."""
    # Create output directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_name = f"tau_bench_{config.env}"
    output_dir = f"./data/{dataset_name}_{timestamp}"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📊 Formatting results from {unformatted_results_path}")
    
    # Load unformatted results
    with open(unformatted_results_path, "r") as f:
        results = json.load(f)
    
    scores = []
    for result in results:
        task_id = result["task_id"]
        reward = result["reward"]
        
        # Create trajectory file
        model_name = config.model.replace("/", "-")
        trajectory_path = f"{output_dir}/{model_name}_task{task_id}_trajectory.jsonl"
        with open(trajectory_path, "w") as f:
            for message in result["traj"]:
                f.write(json.dumps(message) + "\n")
        
        # Collect score information
        task_info = result["info"]["task"]
        
        # Extract actual actions executed by the agent from conversation
        actual_actions = []
        for message in result["traj"]:
            if message.get("role") == "assistant" and message.get("tool_calls"):
                for tool_call in message["tool_calls"]:
                    if tool_call.get("function"):
                        name = tool_call["function"]["name"]
                        args = json.loads(tool_call["function"]["arguments"])
                        actual_actions.append(f"{name}({json.dumps(args)})")
        
        # Get the prompt (task instruction)
        instruction = task_info.get("instruction", "")
        
        # Get the expected actions (ground truth) from the task definition
        expected_actions = []
        if "actions" in task_info:
            for action in task_info["actions"]:
                expected_actions.append(f"{action['name']}({json.dumps(action['kwargs'])})")
        
        score_entry = {
            "task-id": f"task-{task_id}",
            "prompt": instruction,
            "result": ",".join(actual_actions) if actual_actions else "No actions executed",
            "truth": ",".join(expected_actions) if expected_actions else "",
            "score": reward,
            "duration": result["info"].get("duration", 0) if "info" in result else 0
        }
        scores.append(score_entry)
    
    # Create scores file
    model_name = config.model.replace("/", "-")
    scores_path = f"{output_dir}/{model_name}_scores.jsonl"
    with open(scores_path, "w") as f:
        for score in scores:
            f.write(json.dumps(score) + "\n")
    
    print(f"✅ Formatted results saved to {output_dir}")
    print(f"  - Trajectory files: {model_name}_taskN_trajectory.jsonl")
    print(f"  - Scores file: {model_name}_scores.jsonl")


def main():
    config = parse_args()
    results = run(config)
    
    # Find the most recent results file
    if results and len(results) > 0:
        results_dir = config.log_dir
        if os.path.exists(results_dir):
            files = [f for f in os.listdir(results_dir) if f.endswith('.json')]
            if files:
                latest_file = max(files, key=lambda x: os.path.getmtime(os.path.join(results_dir, x)))
                unformatted_results_path = os.path.join(results_dir, latest_file)
                format_results(config, unformatted_results_path)


if __name__ == "__main__":
    main()
