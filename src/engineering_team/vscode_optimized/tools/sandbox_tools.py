"""Sandbox file tools backed by a local Python 3.10 virtual environment."""

from __future__ import annotations

import logging
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from crewai.tools import tool

LOGGER = logging.getLogger("engineering_team.vscode_optimized.sandbox")

PACKAGE_DIR = Path(__file__).resolve().parents[1]
SANDBOX_DIR = PACKAGE_DIR / "sandbox"
GRADIO_REQUIREMENT = "gradio==6.28.0"
RUN_TIMEOUT_SECONDS = 300


def sandbox_python() -> Path:
    """Return the interpreter inside the sandbox virtual environment."""
    if os.name == "nt":
        return SANDBOX_DIR / ".venv" / "Scripts" / "python.exe"
    return SANDBOX_DIR / ".venv" / "bin" / "python"


def _is_reparse_point(path: str) -> bool:
    try:
        attributes = os.lstat(path).st_file_attributes  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _remove_reparse_points(root: Path) -> None:
    """Remove directory junctions before ``rmtree`` walks them.

    A junction left by another tool makes ``shutil.rmtree`` raise
    ``WinError 1920`` on Python 3.10.
    """
    if not root.exists():
        return
    pending = [root]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            continue
        for entry in entries:
            try:
                is_dir = entry.is_dir(follow_symlinks=False)
            except OSError:
                continue
            if not is_dir:
                continue
            if _is_reparse_point(entry.path):
                os.rmdir(entry.path)
            else:
                pending.append(Path(entry.path))


def reset_sandbox() -> None:
    """Replace the sandbox with a new venv that has Gradio installed."""
    LOGGER.info("Resetting sandbox at %s", SANDBOX_DIR)
    if SANDBOX_DIR.exists():
        _remove_reparse_points(SANDBOX_DIR)
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True)
    venv_dir = SANDBOX_DIR / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
    python = sandbox_python()
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", GRADIO_REQUIREMENT], check=True)


def _format_result(returncode: int, stdout: str, stderr: str) -> str:
    return (
        f"Exit code: {returncode}\n\n"
        f"--- stdout ---\n{stdout or '(empty)'}\n\n"
        f"--- stderr ---\n{stderr or '(empty)'}"
    )


@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """List the filenames currently in the sandbox directory.

    Returns:
        A newline-separated list of filenames, or a message if the sandbox is empty.
    """
    if not SANDBOX_DIR.exists():
        return "The sandbox is empty."
    names = sorted(path.name for path in SANDBOX_DIR.iterdir())
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """Read and return the text contents of a file in the sandbox directory.

    Args:
        filename: The name of the file to read (e.g. "solution.py").

    Returns:
        The file's contents, or a message if the file does not exist.
    """
    path = SANDBOX_DIR / filename
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text(encoding="utf-8")


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """Write text to a file in the sandbox directory, replacing any existing file.

    Args:
        filename: The name of the file to write (e.g. "solution.py").
        content: The text content to write.

    Returns:
        A confirmation message.
    """
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    path = SANDBOX_DIR / filename
    path.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """Execute a Python file with the sandbox virtual environment.

    unittest writes results, including failures, to stderr. Both streams are returned.

    Args:
        filename: The name of the Python file to run (e.g. "solution.py").

    Returns:
        A labeled block containing the exit code, stdout, and stderr.
    """
    python = sandbox_python()
    if not python.is_file():
        return (
            "Sandbox interpreter is missing. The sandbox virtual environment "
            "has not been created."
        )
    try:
        result = subprocess.run(
            [str(python), filename],
            cwd=SANDBOX_DIR,
            capture_output=True,
            text=True,
            timeout=RUN_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return (
            f"The script timed out after {RUN_TIMEOUT_SECONDS} seconds.\n\n"
            f"--- stdout so far ---\n{stdout or '(empty)'}\n\n"
            f"--- stderr so far ---\n{stderr or '(empty)'}"
        )
    return _format_result(result.returncode, result.stdout, result.stderr)


sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]


def _never_cache(*_args: object, **_kwargs: object) -> bool:
    return False


for _tool in sandbox_tools:
    _tool.cache_function = _never_cache
