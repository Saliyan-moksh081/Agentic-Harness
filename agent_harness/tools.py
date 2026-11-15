"""Bounded tools used by the PatchPilot ADK agent."""

import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SANDBOX = Path(os.getenv("PATCHPILOT_SANDBOX", PROJECT_ROOT / "sandbox")).resolve()
SAFE_SUFFIXES = {".md", ".py"}
IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__", ".pytest_cache"}
MAX_FILES = 50
MAX_OUTPUT = 4_000


def check_task_contract(task: str, acceptance_criteria: list[str]) -> dict[str, object]:
    """Check that a coding task has a description and acceptance criteria."""
    task = task.strip()
    criteria = [item.strip() for item in acceptance_criteria if item.strip()]
    missing = []
    if not task:
        missing.append("Describe the coding task.")
    if not criteria:
        missing.append("Provide at least one acceptance criterion.")
    return {"ready": not missing, "task": task, "criteria": criteria, "missing": missing}


def _sandbox_path(path: str, writing: bool = False) -> Path:
    relative = Path(path)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("Use a relative path inside the sandbox.")
    if any(part.startswith(".env") for part in relative.parts):
        raise ValueError("Environment files are not available to the agent.")

    target = (SANDBOX / relative).resolve()
    if not target.is_relative_to(SANDBOX.resolve()):
        raise ValueError("Path escapes the sandbox.")
    if target.suffix.lower() not in SAFE_SUFFIXES:
        raise ValueError("Only Markdown and Python files are allowed.")
    if writing and (relative.parts[0] != "src" or target.suffix != ".py"):
        raise ValueError("Writes are allowed only to Python files under sandbox/src/.")
    return target


def inspect_workspace() -> list[str]:
    """List Markdown and Python files in the benchmark sandbox."""
    files = []
    for current, directories, filenames in os.walk(SANDBOX):
        directories[:] = sorted(name for name in directories if name not in IGNORED_DIRECTORIES)
        for filename in sorted(filenames):
            path = Path(current) / filename
            if filename.startswith(".env") or path.suffix.lower() not in SAFE_SUFFIXES:
                continue
            files.append(path.relative_to(SANDBOX).as_posix())
            if len(files) == MAX_FILES:
                return files
    return files


def read_file(path: str) -> dict[str, object]:
    """Read a Markdown or Python file from the benchmark sandbox."""
    try:
        target = _sandbox_path(path)
        content = target.read_text(encoding="utf-8")[:MAX_OUTPUT]
        return {"ok": True, "path": path, "content": content}
    except (OSError, ValueError) as error:
        return {"ok": False, "error": str(error)}


def write_file(path: str, content: str) -> dict[str, object]:
    """Write a Python source file under sandbox/src; tests and other paths are protected."""
    try:
        target = _sandbox_path(path, writing=True)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"ok": True, "path": path}
    except (OSError, ValueError) as error:
        return {"ok": False, "error": str(error)}


def run_quality_gate() -> dict[str, object]:
    """Run the fixed sandbox pytest suite with a 45-second timeout."""
    started = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tests"],
            cwd=SANDBOX,
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "timed_out": True,
            "duration_seconds": round(time.monotonic() - started, 2),
        }
    except OSError as error:
        return {"passed": False, "error": str(error)}

    return {
        "passed": result.returncode == 0,
        "exit_code": result.returncode,
        "duration_seconds": round(time.monotonic() - started, 2),
        "output": (result.stdout + "\n" + result.stderr)[-MAX_OUTPUT:],
    }
