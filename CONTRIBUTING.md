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

- Keep `custom_components/py_sungrow_isolarcloud/` compliant with Home Assistant integration standards (`hassfest` and `hacs`).
- Never commit personal tokens, credentials, plant IDs, or private API captures.
- Keep `strings.json`, `translations/en.json`, and `translations/es.json` in sync whenever adding or renaming entities or config flow fields.
- Add or update unit tests under `tests/` for any new parsing, API, or entity behavior.

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Make focused, well-tested changes.
3. Fill out the pull request template and wait for CI checks (`lint`, `test`, `hassfest`, `hacs`) to pass.
