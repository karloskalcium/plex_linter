set shell := ["bash", "-euo", "pipefail", "-c"]

# List available recipes
default:
    @just --list

# === Quality ===

# Run all checks (lint, typecheck, test)
check: lint typecheck test

# Format code base
format: install
    uv run ruff check --fix
    uv run ruff format

# Lint code base
lint: install
    uv run ruff check
    uv run ruff format --check
    just --fmt --check --unstable

# Runs all tests
test: unit-test

# Run type checker
typecheck: install
    uv run pyright

# Runs python unit tests
unit-test: install
    uv run pytest --cov --cov-report term --cov-report html

# === Dependency Management ===

# Check for outdated GitHub Actions (dry run)
check-actions:
    actions-up --dry-run

# Update pre-commit hooks to latest and freeze revisions to commit SHAs
freeze-hooks:
    pre-commit autoupdate --freeze

# Install dependencies
install:
    uv sync

# Show available package versions (highlights majors outside current specifiers)
outdated:
    uv tree --all-groups --depth 1 --outdated | grep --color=always "(latest:.*)" || true

# Upgrade all dependencies in uv.lock to latest within version specifiers
upgrade:
    uv lock --upgrade
    uv sync

# Upgrade GitHub Actions to latest versions
upgrade-actions:
    actions-up --yes

# === Cleanup ===

# Delete any directories, files or logs that are auto-generated
clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    rm -f .coverage*
    rm -rf results dist .ruff_cache .pytest_cache
    rm -f profile_output*
    rm -f log/plex_linter.log

# Clean all temp files and empty UV caches and virtual environments
deepclean: clean
    rm -rf .venv/
    uv cache clean
    uv cache prune
