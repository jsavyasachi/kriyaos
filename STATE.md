# Kriya OS State

This is the durable handoff file for AI coding sessions. Read this before
touching code. Update it when state, intent, workflow, completed work, blockers,
or next plans change.

## Current Intent

Build Kriya OS as a read-first personal OS:

- collect state from Gmail, Calendar, Google Tasks, Keep, finance, and vitals
- write local summaries under `state/`
- propose actions into `state/pending/*.json`
- require explicit approval before any external write

Default rule: local files are safe; Google writes are not.

## Workflow

1. Use CLI for deterministic human/script/launchd execution.
2. Use Goose MCP tools for conversational agent access.
3. Keep CLI and MCP names conceptually aligned.
4. Add read-only integrations first.
5. Proposed writes go to approval queue only.
6. Deterministic executor comes later and must contain no LLM loop.
7. Keep `state/` gitignored.
8. Run `python -m unittest discover` before committing.
9. Run `uv run --extra dev ruff check .` before committing when lint dependencies are available.
10. Commit with Conventional Commits.
11. Push only when explicitly asked.

## Current Surfaces

CLI:

- `python -m kriya daily-brief`
- `python -m kriya email-triage`
- `python -m kriya tasks`
- `python -m kriya notes`
- `python -m kriya finance`
- `python -m kriya vitals`
- `python -m kriya approvals`
- `python -m kriya approve <id>`
- `python -m kriya execute <id>`
- `python -m kriya reject <id>`
- `python -m kriya sync-tasks`
- `python -m kriya poll`
- `python -m kriya inbox`

MCP tools:

- `daily_brief`
- `email_triage`
- `tasks`
- `notes`
- `finance`
- `vitals`
- `approvals`
- `approve`
- `execute`
- `reject`
- `sync_tasks`
- `poll`
- `inbox`

## Current Local State Model

- `state/daily-brief-YYYY-MM-DD.md` - daily summary
- `state/inbox.md` - appended email triage sections
- `state/tasks-YYYY-MM-DD.md` - Google Tasks snapshot
- `state/notes-YYYY-MM-DD.md` - Google Keep notes snapshot
- `state/finance-YYYY-MM-DD.md` - f5e net-worth snapshot
- `state/vitals-YYYY-MM-DD.md` - Apple Health vitals snapshot
- `state/pending/*.json` - approval-gated proposed writes
- `state/sync/mappings.json` - Google↔Apple sync ID mappings
- `state/runs/*-daily_brief.json` - daily brief idempotency markers
- `state/runs/*-email_triage.json` - email triage idempotency markers
- `state/audit.jsonl` - tool-call audit log
- `state/errors.jsonl` - failure log surfaced in daily brief
- `state/usage.jsonl` - cost accounting used by the daily spend guard

## Completed

- AI-native repo setup with shared `AI.md` symlinks.
- Public GitHub repo.
- Daily brief generator with Calendar, Gmail, Tasks, finance, vitals, and errors.
- `gws` audit logging for Workspace tool calls.
- Error logging and recent-error surfacing in daily brief.
- Idempotency markers for daily brief and email triage.
- Cost ceiling guard via `MAX_DAILY_USD`, default `$2.00`.
- launchd template for daily brief.
- Read-only email triage into `state/inbox.md`.
- Read-only Google Tasks snapshot and daily brief Tasks section.
- Read-only Google Keep notes snapshot and optional daily brief Notes section.
- Approval queue foundation for proposed writes.
- Email triage creates local `tasks.insert` proposals for actionable emails.
- CLI entrypoint.
- Normalized MCP tools.
- `poll` read-only state update loop.
- `inbox` local state renderer.
- Read-only `f5e` finance snapshot and daily brief Finance section.
- Read-only Apple Health vitals snapshot and daily brief Vitals section.
- `poll` snapshots tasks, notes, finance, vitals, email triage, then daily brief.
- Finance/vitals paths are configurable with `KRIYA_F5E_REPO` and `KRIYA_VITALS_DB`.
- Google Workspace and Memory-backed commands fail fast after logging required integration failures.
- Daily brief Memory enrichment is optional: broken Mem0 lookup is logged and omitted.
- Daily brief Keep notes enrichment is optional: missing Keep scope is logged and omitted.
- Approval executor CLI and MCP tools can approve, reject, and execute approved actions.
- Approved `tasks.insert` actions execute through the deterministic executor.
- Pure task sync planner can reconcile normalized Google Tasks and Apple Reminders.
- Google Tasks `update`, `complete`, and `delete` executors are registered.
- Apple Reminders add/update/complete/delete adapters write through `osascript`.
- `sync-tasks` writes Apple-side task changes inline and queues Google-side writes for approval.
- Apple Calendar already reads Google calendars through the local Google account, so calendar sync is deferred unless duplicate-control logic is designed.

## Open Blockers

- Google Keep: current OAuth token may still lack Keep scopes.
  Re-auth with `https://www.googleapis.com/auth/keep.readonly`, then verify
  `gws keep notes list` and `python -m kriya notes`.
- Launchd is scaffolded but not installed/validated as a real user agent.
- Google Keep `Groceries` cannot be read until Keep OAuth is fixed, blocking grocery sync.

## Proposed Next Plan

1. Re-auth Keep and smoke-test `python -m kriya notes`.

2. Change `sync-tasks` wiring from Apple Reminders `Reminders` to Apple Reminders `To do`.

3. Add Google Keep `Groceries` ↔ Apple Reminders `Groceries` sync after Keep auth is fixed.

## Design Notes

- Daily brief is not the OS. It is one scheduled report.
- `poll` should update state. `inbox` should display state.
- The approval queue is the safety boundary between read-only intelligence and
  external writes.
- Goose should call MCP tools; launchd should call CLI commands.
- Current sync routing: Google Tasks `To Do` ↔ Apple Reminders `To do`; Google Keep `Groceries` ↔ Apple Reminders `Groceries`; Apple Reminders `Reminders` is Apple-only.
