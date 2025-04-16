import os
import glob
import json
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional
import subprocess
import threading

app = FastAPI(title="TAU-Bench MT Benchmark API")

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))

run_lock = threading.Lock()

def find_scores_file(model: str, subset: str) -> Optional[str]:
    # Model name is formatted as in output: e.g., openai_gpt-4o, but file uses dashes
    model_dash = model.replace("_", "-")
    pattern = os.path.join(DATA_DIR, f"tau_bench_{subset}_*/{model_dash}_scores.jsonl")
    matches = sorted(glob.glob(pattern), reverse=True)  # latest first
    return matches[0] if matches else None


def filter_scores_by_taskid(scores_path: str, task_id: Optional[str]) -> str:
    if not task_id:
        with open(scores_path, "r") as f:
            return f.read()
    # Filter lines by task-id
    filtered_lines = []
    with open(scores_path, "r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if str(obj.get("task-id", "")).endswith(str(task_id)):
                    filtered_lines.append(json.dumps(obj))
            except Exception:
                continue
    return "\n".join(filtered_lines)


def run_benchmark(model: str, subset: str, task_id: str) -> None:
    # Model param is like openai_gpt-4o; for CLI, convert _ to /
    model_cli = model.replace("_", "/")
    # Map subset to env argument
    env_map = {"airline": "airline", "retail": "retail"}
    env = env_map.get(subset, subset)
    # Compose command
    cmd = [
        "python", "run.py",
        "--model", model_cli,
        "--task-ids", str(task_id)
    ]
    # Set up environment if needed
    env_vars = os.environ.copy()
    # Run the command in a subprocess, blocking until done
    try:
        with run_lock:
            subprocess.run(cmd, check=True, env=env_vars, cwd="/app")
    except Exception as e:
        raise RuntimeError(f"Benchmark run failed: {e}")


@app.get("/scores")
def get_scores(
    model: str = Query(..., description="Model name, e.g. openai_gpt-4o"),
    subset: str = Query(..., description="Subset/environment, e.g. airline or retail"),
    taskID: Optional[str] = Query(None, description="Task ID to filter (optional)")
):
    # Always run the benchmark for every request
    try:
        run_benchmark(model, subset, taskID)
        scores_path = find_scores_file(model, subset)
        if not scores_path or not os.path.exists(scores_path):
            raise HTTPException(status_code=404, detail=f"Scores file not found for model={model}, subset={subset}")
        content = filter_scores_by_taskid(scores_path, taskID)
        return PlainTextResponse(content, media_type="application/jsonl")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Optionally, add endpoints for trajectory files, listing runs, etc.
