import json
import subprocess
from unittest.mock import Mock

from scripts import run_benchmark


def test_benchmark_reports_pass_rate_without_model_calls(tmp_path, monkeypatch):
    tasks = tmp_path / "benchmarks"
    task = tasks / "sample"
    (task / "src").mkdir(parents=True)
    (task / "tests").mkdir()
    (task / "task.md").write_text("Implement the sample task.")

    monkeypatch.setattr(run_benchmark, "ROOT", tmp_path)
    monkeypatch.setattr(run_benchmark, "TASKS", tasks)
    monkeypatch.setattr(run_benchmark.shutil, "which", Mock(return_value="adk"))
    run = Mock(return_value=subprocess.CompletedProcess([], 0, "ok", ""))
    monkeypatch.setattr(run_benchmark.subprocess, "run", run)

    run_benchmark.main()

    report = json.loads((tmp_path / "benchmark-results.json").read_text())
    assert report["pass_rate"] == 1
    assert report["tasks"][0]["task"] == "sample"
    assert run.call_count == 2
