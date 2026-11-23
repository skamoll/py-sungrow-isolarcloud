# Contributing to py-sungrow-isolarcloud

Thank you for your interest in contributing!

## Development Setup

```bash
git clone https://github.com/skamoll/py-sungrow-isolarcloud.git
cd py-sungrow-isolarcloud
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Code Quality & Tests

Before opening a pull request, please ensure all checks pass locally:

```bash
ruff check .
ruff format --check .
pytest -v
```

## Guidelines

- Keep `src/py_sungrow_isolarcloud/` completely independent from Home Assistant (standard async Python + `aiohttp` + `cryptography` only).
- Never commit personal tokens, credentials, plant IDs, or private API captures.
- Add or update unit tests under `tests/` for any new parsing, protocol, or client behavior.

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Make focused, well-tested changes.
3. Fill out the pull request template and wait for CI checks (`lint-and-test`) to pass.
