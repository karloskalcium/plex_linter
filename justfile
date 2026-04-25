set shell := ["bash", "-euo", "pipefail", "-c"]

# List available recipes
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run all checks (lint, typecheck, test)
check: lint typecheck test

# Runs all tests
test: unit-test

# Runs python unit tests
unit-test: install
    uv run pytest --cov --cov-report term --cov-report html

# Lint code base
lint: install
    uv run ruff check
    uv run ruff format --check

# Run type checker
typecheck: install
    uv run pyright

# Format code base
format: install
    uv run ruff check --fix
    uv run ruff format

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
