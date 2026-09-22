"""Same local front door as portal.py, plus a live view of the crew console.

The log box is the text CrewAI's ConsoleFormatter and print() send to the
terminal. It is not a separate status feed.
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

import engineering_team.patch  # noqa: F401  — same MCP name fix main.py applies
from crewai.events.event_listener import EventListener
from engineering_team.crew import EngineeringTeam
from engineering_team.tools.sandbox_tools import SANDBOX_DIR, reset_sandbox

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORTAL_PORT = 7860
APP_PORT = 7861
APP_URL = f"http://127.0.0.1:{APP_PORT}"
_ANSI = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

_lock = threading.Lock()
_app_proc: subprocess.Popen | None = None
_app_log = None


class _Tee:
    """Copy writes to the original stream and to a shared chunk list."""

    def __init__(self, original, chunks: list[str], chunk_lock: threading.Lock) -> None:
        self.original = original
        self.chunks = chunks
        self.chunk_lock = chunk_lock

    @property
    def encoding(self) -> str:
        return getattr(self.original, "encoding", None) or "utf-8"

    def write(self, data: str) -> int:
        text = data if isinstance(data, str) else str(data)
        with self.chunk_lock:
            self.chunks.append(text)
        self.original.write(text)
        self.original.flush()
        return len(text)

    def flush(self) -> None:
        self.original.flush()

    def isatty(self) -> bool:
        return False


def _load_env() -> None:
    candidates = [
        PROJECT_ROOT / ".env",
        PROJECT_ROOT.parent.parent / ".env",
    ]
    for path in candidates:
        if path.is_file():
            load_dotenv(path, override=False)


def _is_reparse_point(path: str) -> bool:
    try:
        attributes = os.lstat(path).st_file_attributes  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def _remove_reparse_points(root: Path) -> None:
    """Drop broken junctions (for example a Linux .venv lib64) so reset can delete the tree."""
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
                try:
                    os.rmdir(entry.path)
                except OSError:
                    subprocess.run(["cmd", "/c", "rmdir", entry.path], check=False)
            else:
                pending.append(Path(entry.path))


def _stop_generated_app() -> None:
    global _app_proc, _app_log
    proc = _app_proc
    _app_proc = None
    if proc is not None and proc.poll() is None:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                check=False,
                capture_output=True,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
    if _app_log is not None:
        _app_log.close()
        _app_log = None


def _log_tail(limit: int = 40) -> str:
    log_path = SANDBOX_DIR / "portal_app.log"
    if not log_path.is_file():
        return "(no log)"
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-limit:]) or "(empty log)"


def _wait_until_up(proc: subprocess.Popen, seconds: int = 90) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(APP_URL, timeout=2) as response:
                if response.status < 500:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(1)
    return False


def _start_generated_app() -> str:
    global _app_proc, _app_log
    app_file = SANDBOX_DIR / "app.py"
    if not app_file.is_file():
        return (
            "The crew finished, but `sandbox/app.py` was not created, "
            "so there is no app to launch."
        )

    _stop_generated_app()
    log_path = SANDBOX_DIR / "portal_app.log"
    _app_log = open(log_path, "w", encoding="utf-8")
    env = os.environ.copy()
    env["GRADIO_SERVER_NAME"] = "127.0.0.1"
    env["GRADIO_SERVER_PORT"] = str(APP_PORT)
    env["PYTHONUNBUFFERED"] = "1"

    _app_proc = subprocess.Popen(
        ["uv", "run", "app.py"],
        cwd=SANDBOX_DIR,
        env=env,
        stdout=_app_log,
        stderr=subprocess.STDOUT,
    )
    if _wait_until_up(_app_proc):
        return (
            "Build finished. The generated app is running on this machine.\n\n"
            f"[Open the app]({APP_URL})\n\n"
            f"`{APP_URL}`"
        )
    code = _app_proc.poll()
    return (
        "The crew wrote `sandbox/app.py`, but it did not stay up on "
        f"{APP_URL}. Process exit code: {code}.\n\n"
        "```\n"
        f"{_log_tail()}\n"
        "```"
    )


def _visible_log(chunks: list[str], chunk_lock: threading.Lock) -> str:
    with chunk_lock:
        text = "".join(chunks)
    text = _ANSI.sub("", text)
    if len(text) > 150_000:
        text = text[-150_000:]
    return text


def _run_crew(text: str, chunks: list[str], chunk_lock: threading.Lock) -> str:
    listener = EventListener()
    console = listener.formatter.console
    previous_file = console.file
    previous_out = sys.stdout
    previous_err = sys.stderr
    capture_out = _Tee(previous_out, chunks, chunk_lock)
    capture_err = _Tee(previous_err, chunks, chunk_lock)
    console.file = capture_out
    sys.stdout = capture_out
    sys.stderr = capture_err
    try:
        os.chdir(PROJECT_ROOT)
        _stop_generated_app()
        _remove_reparse_points(SANDBOX_DIR)
        reset_sandbox()
        EngineeringTeam().crew().kickoff(inputs={"requirements": text})
        return _start_generated_app()
    finally:
        sys.stdout = previous_out
        sys.stderr = previous_err
        console.file = previous_file


def build_and_launch(requirements: str):
    text = (requirements or "").strip()
    if not text:
        yield "Enter the requirements first.", ""
        return
    if not _lock.acquire(blocking=False):
        yield "A build is already running. Wait for it to finish.", ""
        return

    chunks: list[str] = []
    chunk_lock = threading.Lock()
    holder: dict[str, str] = {}
    done = threading.Event()

    def worker() -> None:
        try:
            holder["result"] = _run_crew(text, chunks, chunk_lock)
        except Exception as exc:
            holder["result"] = (
                "The build failed before an app link was available.\n\n"
                f"`{exc}`"
            )
        finally:
            done.set()
            _lock.release()

    threading.Thread(target=worker, daemon=True).start()
    yield "Crew is running. Agent output appears below as it is printed.", ""
    while not done.wait(1):
        yield "Crew is running. Agent output appears below as it is printed.", _visible_log(
            chunks, chunk_lock
        )
    yield holder.get("result", "The build ended without a result."), _visible_log(
        chunks, chunk_lock
    )


def main() -> None:
    import gradio as gr

    _load_env()
    os.chdir(PROJECT_ROOT)

    with gr.Blocks(title="Engineering Team") as demo:
        gr.Markdown(
            "# Engineering Team\n"
            "Type the system requirements. This page runs the existing crew, "
            "shows the same console output the terminal prints, then starts the "
            "Gradio app the crew wrote and gives you the local link.\n\n"
            "The build usually takes many minutes. Docker Desktop must be running, "
            "because the crew executes sandbox code in Docker. "
            f"Do not run `uv run portal` at the same time. This page uses port {PORTAL_PORT}. "
            f"The built app uses port {APP_PORT}."
        )
        requirements = gr.Textbox(
            label="Requirements",
            lines=14,
            placeholder="Describe the system the crew should build.",
        )
        build = gr.Button("Build app", variant="primary")
        result = gr.Markdown("Idle.")
        logs = gr.Textbox(label="Agent console", lines=24, max_lines=24)
        build.click(build_and_launch, inputs=requirements, outputs=[result, logs])

    demo.queue(default_concurrency_limit=1)
    demo.launch(server_name="127.0.0.1", server_port=PORTAL_PORT)


if __name__ == "__main__":
    main()
