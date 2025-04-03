# τ-bench: Modified for MT Benchmark Integration

This repository is a fork of [τ-bench](https://arxiv.org/abs/2406.12045) modified to work with the MT Benchmark evaluation framework.

## Modifications Made

1. **Output Formatting**: Added formatting to match MT Benchmark schema
2. **Configuration**: Simplified to use YAML config and minimal CLI arguments
3. **Error Handling**: Fixed response cost tracking and directory creation

## Input/Output Schema

### Input Schema
```json
{
    "dataset_name": "tau_bench",    // Which benchmark to run
    "model_name": "gpt-4o",         // Model to evaluate
    "subsets": "retail"             // Task subset to run (retail/airline)
}
```

### Output Schema
The benchmark produces formatted results in `./data/{dataset_name}_{timestamp}/`:

1. **Trajectory Files**: `{model}_task{id}_trajectory.jsonl`
   ```json
   {"role": "system", "content": "You are a helpful assistant..."}
   {"role": "user", "content": "Help me book a flight..."}
   {"role": "assistant", "content": "I'd be happy to help you book a flight..."}
   ```

2. **Scores File**: `{model}_scores.jsonl`
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

## Running the Benchmark

```bash
python run.py --model openai/gpt-4o --task-ids 1 2 3
```

## Error Handling and Retries

When running the benchmark, you may encounter network errors or API failures, especially with external model providers. The benchmark will output error messages for failed tasks. To handle these failures:

1. **Retry Specific Task IDs**: If certain tasks fail, you can re-run just those specific tasks:
   ```bash
   python run.py --model openai/gpt-4o --task-ids 2  # Retry only task ID 2
   ```

2. **Common Errors**:
   - SSL/Network errors: Usually temporary and can be resolved by retrying
   - Rate limiting: Wait a few minutes before retrying
   - Authentication errors: Check your API keys in the config file

The formatted results will be updated with any successfully completed tasks.

## Next Steps

### 1. API Integration for Data Access

We need to implement an API endpoint in the tau-bench Docker container to serve the `./data/` directory to go-evaluator. Options include:

- **REST API**: Add a simple Flask/FastAPI server to expose endpoints for:
  - Listing available benchmark runs
  - Retrieving trajectory and score files
  - Triggering new benchmark runs

- **File System Mount**: Alternatively, configure Docker volume mounting to share the data directory directly with go-evaluator

### 2. LLMServer Integration

Replace the current litellm implementation with our LLMServer:

1. Modify `tau_bench/agents/tool_calling_agent.py` to use our LLMServer instead of litellm
2. Update `tau_bench/envs/user.py` to use our LLMServer for user simulation
3. Configure proper authentication and routing between containers

This approach will allow us to:
- Use our own LLM infrastructure
- Track token usage and costs centrally
- Ensure consistent model behavior across benchmarks

## Setup

1. Clone this repository
2. Install with `pip install -e .`
3. Configure API keys in `.env`

## Citation

```bibtex
@misc{yao2024tau,
      title={$\tau$-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains}, 
      author={Shunyu Yao and Noah Shinn and Pedram Razavi and Karthik Narasimhan},
      year={2024},
      eprint={2406.12045},
      archivePrefix={arXiv},
      primaryClass={cs.AI}
}
