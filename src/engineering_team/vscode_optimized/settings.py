"""Runtime configuration loaded from the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[2]

DEFAULT_REQUIREMENTS = """
A simple HR desk system for managing employees and leave.
The system should allow creating an employee with id, name, and department.
The system should allow assigning annual leave days and recording leave taken.
The system should calculate remaining leave balance.
The system should report all employees in a department and list leave history for an employee.
The system should prevent leave that exceeds remaining balance or creating a duplicate employee id.
The system has access to a function get_default_leave_days(department) which returns fixed leave entitlements for Engineering, Sales, and HR.
""".strip()


@dataclass(frozen=True)
class Settings:
    """Values required to start the crew."""

    gemini_api_key: str
    requirements: str


def load_settings() -> Settings:
    """Load ``.env`` files and require ``GEMINI_API_KEY``.

    A package-level ``.env`` is loaded first, then the repository ``.env``.
    Existing process environment variables are left unchanged.
    """
    load_dotenv(PACKAGE_DIR / ".env", override=False)
    load_dotenv(REPO_ROOT / ".env", override=False)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Copy "
            "src/engineering_team/vscode_optimized/.env.example to .env and set the key."
        )

    requirements = os.environ.get("ENGINEERING_REQUIREMENTS", "").strip()
    return Settings(
        gemini_api_key=api_key,
        requirements=requirements or DEFAULT_REQUIREMENTS,
    )
