import subprocess
import sys
from unittest.mock import patch

from agent_harness import tools


def test_task_contract_requires_criteria():
    result = tools.check_task_contract("Fix palindrome", [])
    assert result["ready"] is False
    assert result["missing"]


def test_write_file_allows_only_sandbox_source(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "SANDBOX", tmp_path)

    result = tools.write_file("src/example.py", "answer = 42")
    blocked = tools.write_file("tests/test_example.py", "assert True")

    assert result["ok"] is True
    assert (tmp_path / "src/example.py").read_text() == "answer = 42"
    assert blocked["ok"] is False
    assert not (tmp_path / "tests/test_example.py").exists()


def test_read_file_blocks_paths_outside_sandbox(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "SANDBOX", tmp_path)

    result = tools.read_file("../secret.py")

    assert result["ok"] is False


def test_write_file_blocks_symlink_escape(tmp_path, monkeypatch):
    sandbox = tmp_path / "sandbox"
    outside = tmp_path / "outside.py"
    (sandbox / "src").mkdir(parents=True)
    outside.write_text("unchanged")
    (sandbox / "src" / "link.py").symlink_to(outside)
    monkeypatch.setattr(tools, "SANDBOX", sandbox)

    result = tools.write_file("src/link.py", "overwritten")

    assert result["ok"] is False
    assert outside.read_text() == "unchanged"


def test_inspection_skips_env_and_generated_directories(tmp_path, monkeypatch):
    monkeypatch.setattr(tools, "SANDBOX", tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "src" / "app.py").write_text("safe")
    (tmp_path / ".env").write_text("secret")
    (tmp_path / ".venv" / "hidden.py").write_text("generated")

    files = tools.inspect_workspace()

    assert files == ["src/app.py"]


def test_quality_gate_uses_fixed_command_and_timeout():
    result_from_pytest = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="3 passed", stderr=""
    )
    with patch.object(tools.subprocess, "run", return_value=result_from_pytest) as run:
        result = tools.run_quality_gate()

    assert result["passed"] is True
    assert run.call_args.args[0] == [sys.executable, "-m", "pytest", "-q", "tests"]
    assert run.call_args.kwargs["cwd"] == tools.SANDBOX
    assert run.call_args.kwargs["timeout"] == 45


def test_quality_gate_reports_timeout(monkeypatch):
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired("pytest", 45)

    monkeypatch.setattr(tools.subprocess, "run", timeout)
    result = tools.run_quality_gate()

    assert result["passed"] is False
    assert result["timed_out"] is True
