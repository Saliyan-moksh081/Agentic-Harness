# PatchPilot

PatchPilot is a coding-agent benchmark built with Google ADK and Amazon Bedrock. It demonstrates how a harness can bound an agent's tools and independently verify its code with tests.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Set `AWS_BEARER_TOKEN_BEDROCK`, `AWS_REGION_NAME`, and `BEDROCK_MODEL_ID` in `.env`. Keep `.env` private; `.env.example` shows the required variable names.

Run the interactive agent:

```bash
adk run agent_harness
```

Try: `Implement the Slugify task in sandbox/README.md. The acceptance criteria are in that file.` The agent should inspect the sandbox, edit source code, run its tests, and report the result.

For ADK's browser UI and execution traces, run `adk web agent_harness`.

## How a run works

1. The user gives the ADK agent a coding task and acceptance criteria.
2. The agent calls `check_task_contract` to check that both are present.
3. It uses `inspect_workspace` and `read_file` to understand the sandbox.
4. It proposes a source change through `write_file`.
5. It calls `run_quality_gate`, which runs the sandbox's pytest suite.
6. The agent reports the test result returned by the tool.

The agent is a Google ADK `LlmAgent`. ADK's `LiteLlm` connector routes model requests to `bedrock/global.openai.gpt-6-luna`.

## Tool boundaries

- The agent can inspect Markdown and Python files in the active sandbox.
- It can write only Python files under `src/`; test files cannot be written through the tool.
- Paths are resolved and checked to prevent `..` and symlink escapes.
- `.env` files are not available to the agent.
- Test execution is a fixed `python -m pytest -q tests` command with a 45-second timeout. The agent cannot provide arbitrary shell commands.
- Repository file contents are treated as data, not as instructions.

These boundaries are enforced in `agent_harness/tools.py`; the agent instructions alone are not the security mechanism.

## Interactive sandbox and benchmark fixtures

- `sandbox/` is used by `adk run` and `adk web`. Changes made there remain in that directory.
- `benchmarks/palindrome/` and `benchmarks/slugify/` are templates. `scripts/run_benchmark.py` copies each to a fresh temporary directory before running the agent, so changes cannot leak between tasks or alter the templates.
- Each benchmark contains a `task.md`, starter Python code, and tests. The agent runs the test gate in its temporary workspace; the benchmark runner then runs the tests independently. A task passes only if both the agent process and tests exit successfully.

## Run checks and benchmarks

Run the offline harness tests (no Bedrock calls):

```bash
python -m pytest -q
```

Run the benchmark suite:

```bash
python scripts/run_benchmark.py
```

Each task starts an ADK agent session, which may make multiple Bedrock requests and incur model usage charges. The runner records pass rate and per-task duration in the ignored local file `benchmark-results.json`.

## What we've built

- Connected the ADK agent to the requested Bedrock model using local environment variables.
- Added task-contract, workspace-inspection, file-read, file-write, and test-runner tools.
- Restricted source writes to the sandbox and protected tests from writes through the agent tool.
- Added palindrome and slugify benchmark tasks with deterministic pytest checks.
- Added a benchmark runner that uses a fresh workspace per task and records pass rate and duration.
- Added offline tests for tool boundaries, ADK agent setup, and benchmark aggregation.

## Latest benchmark result

The latest local report showed **2/2 tasks passing (100%)**:

| Task | Result | Duration |
| --- | --- | ---: |
| palindrome | Pass | 11.45 s |
| slugify | Pass | 12.74 s |

Duration includes the agent session and independent test run. This is one run of two small tasks—not enough evidence to claim a general reliability improvement. The report does not currently capture token usage or model cost.

## Next steps

Add more varied coding tasks, run each task repeatedly, and compare harness configurations. Track failures and token/cost usage as well as pass rate and duration before presenting reliability claims on a resume.
