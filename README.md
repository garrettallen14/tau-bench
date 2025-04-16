# τ-bench: MT Benchmark Integration

This repository is a fork of [τ-bench](https://arxiv.org/abs/2406.12045) adapted for the MT Benchmark evaluation framework.

## Key Modifications
- **MT Benchmark Output**: Results and trajectories match the MT Benchmark schema.
- **Simplified Configuration**: YAML config and minimal CLI arguments.
- **Robust Error Handling**: Improved response cost tracking and directory creation.

## Input/Output Schema

**Input Example:**
```json
{
  "dataset_name": "tau_bench",
  "model_name": "gpt-4o",
  "subsets": "retail"
}
```

**Output:**
- Results in `./data/{dataset_name}_{timestamp}/`
- **Trajectory Files**: `{model}_task{id}_trajectory.jsonl`
- **Scores File**: `{model}_scores.jsonl`

**Trajectory Example:**
```json
{"role": "system", "content": "You are a helpful assistant..."}
{"role": "user", "content": "Help me book a flight..."}
{"role": "assistant", "content": "I'd be happy to help you book a flight..."}
```

**Scores Example:**
```json
{
  "task-id": "task-1",
  "prompt": "task description",
  "result": "action1({...}),action2({...})",
  "truth": "expected_action1({...}),expected_action2({...})",
  "score": 1.0,
  "duration": 100
}
```

## Running the Benchmark (Locally)

```bash
python run.py --model openai/gpt-4o --task-ids 1 2 3
```

- To retry a specific task:  
  `python run.py --model openai/gpt-4o --task-ids 2`

Common errors (network, rate limit, auth) will be surfaced in output and can be resolved by retrying or checking credentials.

## Dockerized API Usage

### Build and Run

1. Build the image:
   ```bash
   docker build -t tau-bench-api .
   ```
2. Run the container (with data persistence and env vars):
   ```bash
   docker run -p 8000:8000 -v $(pwd)/data:/app/data --env-file .env tau-bench-api
   ```

### Querying Results via API

Every API call triggers a fresh benchmark run and returns the latest results for your query.

```bash
curl "http://localhost:8000/scores?model=openai_gpt-4o&subset=airline&taskID=1"
```
- `model`: Model name, e.g. `openai_gpt-4o`
- `subset`: Environment, e.g. `airline` or `retail`
- `taskID`: (Optional) Specific task ID

Returns: `/data/{model}_scores.jsonl` (filtered by `taskID` if provided) as JSONL.

**Example Response:**
```
{"task-id": "task-1", "prompt": "task description", ...}
{"task-id": "task-2", "prompt": "...", ...}
```

**Notes:**
- The API is implemented in `serve.py` using FastAPI.
- The container exposes port 8000.
- Integrates smoothly with go-evaluator and other orchestrators.

## Next Steps / Customization

### Data Access
- The API endpoint `/scores` always triggers a new benchmark run and returns the result.
- For advanced access (listing runs, retrieving trajectories), extend the API with new endpoints as needed.

### LLMServer Integration
- To use your own LLM server, update `tau_bench/agents/tool_calling_agent.py` and `tau_bench/envs/user.py` to call your backend instead of litellm.
- Configure authentication and routing as required for your infra.

## Setup

1. Clone this repository
2. Install dependencies: `pip install -e .`
3. Add your API keys and credentials to `.env`

## Citation
```bibtex
@misc{yao2024tau,
      title={\$\tau\$-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains}, 
      author={Shunyu Yao and Noah Shinn and Pedram Razavi and Karthik Narasimhan},
      year={2024},
      eprint={2406.12045},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
