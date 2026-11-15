"""Run each coding benchmark in a fresh temporary workspace."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "benchmarks"


def main() -> None:
    adk = shutil.which("adk")
    if not adk:
        raise SystemExit("Activate the project virtual environment first (source .venv/bin/activate).")

    results = []
    for task_dir in sorted(path for path in TASKS.iterdir() if path.is_dir()):
        with tempfile.TemporaryDirectory(prefix="patchpilot-") as workspace:
            shutil.copytree(task_dir, workspace, dirs_exist_ok=True)
            env = {**os.environ, "PATCHPILOT_SANDBOX": workspace}
            prompt = task_dir.joinpath("task.md").read_text(encoding="utf-8")
            started = time.monotonic()

            try:
                agent = subprocess.run(
                    [adk, "run", "--in_memory", "--timeout", "120s", "agent_harness", prompt],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False,
                )
                agent_exit = agent.returncode
            except subprocess.TimeoutExpired:
                agent_exit = -1

            try:
                tests = subprocess.run(
                    [sys.executable, "-m", "pytest", "-q", "tests"],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    timeout=45,
                    check=False,
                )
                test_exit = tests.returncode
            except subprocess.TimeoutExpired:
                test_exit = -1

            passed = agent_exit == 0 and test_exit == 0
            result = {
                "task": task_dir.name,
                "passed": passed,
                "agent_exit_code": agent_exit,
                "test_exit_code": test_exit,
                "duration_seconds": round(time.monotonic() - started, 2),
            }
            results.append(result)
            print(f"{'PASS' if passed else 'FAIL'} {task_dir.name}: {result['duration_seconds']}s")

    report = {"pass_rate": sum(row["passed"] for row in results) / len(results), "tasks": results}
    (ROOT / "benchmark-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Pass rate: {report['pass_rate']:.0%}; report: benchmark-results.json")


if __name__ == "__main__":
    main()
