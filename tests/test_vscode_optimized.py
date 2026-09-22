"""Tests for configuration, imports, crew setup, and the run entry point."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engineering_team.vscode_optimized.settings import (
    PACKAGE_DIR,
    DEFAULT_REQUIREMENTS,
    load_settings,
)

CONFIG_DIR = PACKAGE_DIR / "config"


def test_configuration_files_define_the_crew() -> None:
    agents = yaml.safe_load((CONFIG_DIR / "agents.yaml").read_text(encoding="utf-8"))
    tasks = yaml.safe_load((CONFIG_DIR / "tasks.yaml").read_text(encoding="utf-8"))

    assert set(agents) == {
        "engineering_lead",
        "backend_engineer",
        "frontend_engineer",
        "test_engineer",
    }
    assert set(tasks) == {"design_task", "code_task", "frontend_task", "test_task"}
    for name, spec in agents.items():
        assert spec["llm"] == "gemini/gemini-3.5-flash-lite", name
    assert tasks["design_task"]["agent"] == "engineering_lead"
    assert "{requirements}" in tasks["design_task"]["description"]
    assert "uv project" not in tasks["design_task"]["description"]
    assert "Do not call uv." in tasks["design_task"]["description"]


def test_imports() -> None:
    import engineering_team.vscode_optimized.main as main
    import engineering_team.vscode_optimized.crew as crew

    assert callable(main.main)
    assert crew.EngineeringTeam.__name__ == "EngineeringTeam"


def test_settings_reject_a_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "engineering_team.vscode_optimized.settings.load_dotenv",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        load_settings()


def test_settings_load_the_key_and_default_requirements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "engineering_team.vscode_optimized.settings.load_dotenv",
        lambda *_args, **_kwargs: False,
    )
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.delenv("ENGINEERING_REQUIREMENTS", raising=False)

    settings = load_settings()

    assert settings.gemini_api_key == "test-key"
    assert settings.requirements == DEFAULT_REQUIREMENTS


def test_agent_initialization(monkeypatch: pytest.MonkeyPatch) -> None:
    from crewai.mcp.tool_resolver import MCPToolResolver

    from engineering_team.vscode_optimized.crew import EngineeringTeam

    monkeypatch.setattr(MCPToolResolver, "_resolve_external", lambda _self, _ref: [])
    built = EngineeringTeam().crew()

    assert len(built.agents) == 4
    assert len(built.tasks) == 4
    assert built.process.value == "sequential"


def test_execute_resets_the_sandbox_and_runs_kickoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from engineering_team.vscode_optimized import main

    calls: dict[str, object] = {}

    class _Crew:
        def kickoff(self, inputs: dict[str, str]) -> str:
            calls["inputs"] = inputs
            return "crew-finished"

    monkeypatch.setattr(main, "reset_sandbox", lambda: calls.setdefault("reset", True))
    monkeypatch.setattr(main.os, "chdir", lambda _path: None)
    monkeypatch.setattr(main.EngineeringTeam, "crew", lambda _self: _Crew())

    result = main.execute("build a ledger")

    assert calls["reset"] is True
    assert calls["inputs"] == {"requirements": "build a ledger"}
    assert result == "crew-finished"


def test_sandbox_reset_uses_venv_and_pip() -> None:
    import inspect

    import engineering_team.vscode_optimized.tools.sandbox_tools as sandbox_tools

    source = inspect.getsource(sandbox_tools.reset_sandbox)
    assert "venv" in source
    assert "pip" in source
    assert '"uv"' not in source
    assert sandbox_tools.SANDBOX_DIR == PACKAGE_DIR / "sandbox"
    assert sandbox_tools.sandbox_python().name.startswith("python")


def test_package_layout() -> None:
    assert (PACKAGE_DIR / "main.py").is_file()
    assert (PACKAGE_DIR / ".env.example").is_file()
    assert "GEMINI_API_KEY=" in (PACKAGE_DIR / ".env.example").read_text(encoding="utf-8")
    assert Path("requirements.txt").is_file() or (PACKAGE_DIR.parents[2] / "requirements.txt").is_file()
