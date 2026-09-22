"""Entry point for the VS Code engineering crew.

Run from the repository root:

    python -m engineering_team.vscode_optimized.main
"""

from __future__ import annotations

import os
import sys
from typing import Any

from engineering_team.vscode_optimized.crew import EngineeringTeam
from engineering_team.vscode_optimized.logging_config import configure_logging
from engineering_team.vscode_optimized.settings import PACKAGE_DIR, load_settings
from engineering_team.vscode_optimized.tools.sandbox_tools import reset_sandbox

LOGGER = configure_logging()


def execute(requirements: str) -> Any:
    """Reset the sandbox and run the crew with ``requirements``."""
    os.chdir(PACKAGE_DIR)
    LOGGER.info("Working directory set to %s", PACKAGE_DIR)
    try:
        reset_sandbox()
        return EngineeringTeam().crew().kickoff(inputs={"requirements": requirements})
    except Exception as exc:
        raise RuntimeError(f"An error occurred while running the crew: {exc}") from exc


def main() -> None:
    """Load configuration and run the crew."""
    settings = load_settings()
    LOGGER.info("Starting engineering crew")
    result = execute(settings.requirements)
    LOGGER.info("Crew finished")
    if result is not None:
        sys.stdout.write(f"{result}\n")


if __name__ == "__main__":
    main()
