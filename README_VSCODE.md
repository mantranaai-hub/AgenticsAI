# Engineering team (VS Code, Python 3.10)

This package runs the same engineering crew as `uv_optimized/engineering_team`, using the standard library `venv` and `pip`. It does not use `uv`.

`uv_optimized/` is a separate project and is not required to run this one.

## Setup

From the repository root:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
copy src\engineering_team\vscode_optimized\.env.example .env
```

Set `GEMINI_API_KEY` in `.env`. If the repository root `.env` already contains that key, this package loads it and you can skip the copy.

## Run

```powershell
python -m engineering_team.vscode_optimized.main
```

The integrated terminal uses the `.venv` interpreter configured in `.vscode/settings.json`.

The crew writes the generated application under `src/engineering_team/vscode_optimized/sandbox/`. That sandbox has its own virtual environment, created with `python -m venv` and `pip install gradio==6.28.0`.

## Debug

1. Open this folder in VS Code.
2. Select the interpreter `.venv\Scripts\python.exe` if it is not already selected.
3. Press F5 and choose **Engineering team**.

## Test

```powershell
python -m pytest
```

Or press F5 and choose **Pytest**.
