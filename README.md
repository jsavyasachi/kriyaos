# kriyaos

Agentic personal OS.

## Stack

<a href="https://goose-docs.ai/"><img src="https://img.shields.io/badge/Goose-000000?style=flat&logo=block&logoColor=white" alt="Goose" /></a>
<a href="https://mem0.ai/"><img src="https://img.shields.io/badge/Mem0-000000?style=flat&logo=database&logoColor=white" alt="Mem0" /></a>
<a href="https://python.org/"><img src="https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white" alt="Python" /></a>

## Commands

- `python -m kriya daily-brief`
- `python -m kriya email-triage`
- `python -m kriya tasks`
- `python -m kriya finance`
- `python -m kriya vitals`
- `python -m kriya approvals`
- `python -m kriya poll`
- `python -m kriya inbox`

## Configuration

- `KRIYA_F5E_REPO`: f5e repo path, defaults to `/Users/savya/projects/f5e`
- `KRIYA_VITALS_DB`: Apple Health SQLite path, defaults to `/Users/savya/projects/vitals/health.db`

## Development

- `python -m unittest discover`
- `uv run --extra dev ruff check .`
