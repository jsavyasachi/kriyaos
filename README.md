# kriyaos

Agentic personal OS.

## Stack

<a href="https://goose-docs.ai/"><img src="https://img.shields.io/badge/Goose-000000?style=flat&logo=block&logoColor=white" alt="Goose" /></a>
<a href="https://mem0.ai/"><img src="https://img.shields.io/badge/Mem0-000000?style=flat&logo=database&logoColor=white" alt="Mem0" /></a>
<a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white" alt="Python" /></a>
<a href="https://textual.textualize.io/"><img src="https://img.shields.io/badge/Textual-2E8B57?style=flat&logo=python&logoColor=white" alt="Textual" /></a>

## Commands

- `python -m kriya daily-brief`
- `python -m kriya email-triage`
- `python -m kriya tasks`
- `python -m kriya groceries`
- `python -m kriya finance`
- `python -m kriya vitals`
- `python -m kriya approvals`
- `python -m kriya approve <id>`
- `python -m kriya execute <id>`
- `python -m kriya reject <id>`
- `python -m kriya sync-tasks`
- `python -m kriya poll`
- `python -m kriya inbox`
- `python -m kriya tui`

## TUI

- Install: `pip install -e ".[tui]"`
- Launch: `python -m kriya tui`

## Configuration

- `KRIYA_F5E_REPO`: f5e repo path, defaults to `/Users/savya/projects/f5e`
- `KRIYA_VITALS_DB`: Apple Health SQLite path, defaults to `/Users/savya/projects/vitals/health.db`

## Development

- `python -m unittest discover`
- `uv run --extra dev ruff check .`
