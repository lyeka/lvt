# Repository Guidelines

This guide helps contributors develop, test, and extend this project efficiently.

## Project Structure & Module Organization
- Source in `src/` with modules: `agents/`, `service/`, `client/`, `core/`, `schema/`, `memory/`.
- Entrypoints: `src/run_service.py` (FastAPI API), `src/streamlit_app.py` (UI), `src/run_client.py` (examples).
- Tests in `tests/` mirroring `src/`. Dev/ops: `compose.yaml`, `docker/`, `.pre-commit-config.yaml`, `.env.example`.

## Build, Test, and Development Commands
- Setup env: `uv sync --frozen && source .venv/bin/activate`.
- Run API: `python src/run_service.py` (serves `http://0.0.0.0:8080`).
- Run UI: `streamlit run src/streamlit_app.py` (default `http://localhost:8501`).
- Docker dev (hot reload): `docker compose watch`.
- Unit tests: `pytest -q`. Coverage: `pytest --cov=src --cov-report=term-missing`.
- Docker integration tests: `pytest -m docker --run-docker` (ensure `docker compose watch` running).

## Coding Style & Naming Conventions
- Python ≥ 3.11, 4‑space indentation, type hints where practical.
- Lint/format with Ruff (line length 100, target `py311`):
  - `ruff check . --fix && ruff format .`
  - Install hooks: `pre-commit install`; run all: `pre-commit run -a`.
- Naming: functions/modules `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Structure: mirror `src/`; files named `test_*.py`; async tests use `@pytest.mark.asyncio`.
- Env isolation defaults set in `tests/conftest.py`.
- CI enforces coverage; >2% total drop flagged.

## Commit & Pull Request Guidelines
- Use Conventional Commits (e.g., `feat:`, `fix:`, `docs:`, `test:`). Keep commits scoped and atomic.
- PRs include summary, rationale, linked issues, and screenshots for UI changes.
- Required before submitting: clean lint (`ruff`), formatted code, tests pass locally (include `--run-docker` when relevant).

## Security & Configuration Tips
- Never commit real secrets. Copy `.env.example` to `.env` and configure locally.
- Dev-only credentials live under `privatecredentials/` (mounted by Docker).
- Adding agents: place code in `src/agents/` and register in `src/agents/agents.py` to appear in `/info`.

