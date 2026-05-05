# Kriya OS State

This is the durable handoff file for AI coding sessions. Read this before
touching code. Update it when state, intent, workflow, completed work, blockers,
or next plans change.

## Current Intent

Build Kriya OS as a read-first personal OS:

- collect state from Gmail, Calendar, Google Tasks, finance, vitals, and later Keep
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
9. Commit with Conventional Commits.
10. Push only when explicitly asked.

## Current Surfaces

CLI:

- `python -m kriya daily-brief`
- `python -m kriya email-triage`
- `python -m kriya tasks`
- `python -m kriya finance`
- `python -m kriya vitals`
- `python -m kriya approvals`
- `python -m kriya poll`
- `python -m kriya inbox`

MCP tools:

- `daily_brief`
- `email_triage`
- `tasks`
- `finance`
- `vitals`
- `approvals`
- `poll`
- `inbox`

## Current Local State Model

- `state/daily-brief-YYYY-MM-DD.md` - daily summary
- `state/inbox.md` - appended email triage sections
- `state/tasks-YYYY-MM-DD.md` - Google Tasks snapshot
- `state/finance-YYYY-MM-DD.md` - f5e net-worth snapshot
- `state/vitals-YYYY-MM-DD.md` - Apple Health vitals snapshot
- `state/pending/*.json` - approval-gated proposed writes
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
- Approval queue foundation for proposed writes.
- Email triage creates local `tasks.insert` proposals for actionable emails.
- CLI entrypoint.
- Normalized MCP tools.
- `poll` read-only state update loop.
- `inbox` local state renderer.
- Read-only `f5e` finance snapshot and daily brief Finance section.
- Read-only Apple Health vitals snapshot and daily brief Vitals section.

## Open Blockers

- Google Keep: `gws` exposes `keep`, but current OAuth token lacks Keep scopes.
  Re-auth with `https://www.googleapis.com/auth/keep.readonly`, verify
  `gws keep notes list`, then add Keep read-only summary.
- Finance/vitals external repo paths are hardcoded for now:
  `/Users/savya/projects/f5e` and `/Users/savya/projects/vitals/health.db`.
  Make them configurable with `KRIYA_F5E_REPO` and `KRIYA_VITALS_DB`.
- Launchd is scaffolded but not installed/validated as a real user agent.
- Approval executor does not exist yet. Pending items cannot be approved into
  real Google writes.

## Proposed Next Plan

1. Add approval executor skeleton.
   - commands: `approve <id>`, `reject <id>`
   - start with status transitions only
   - no Google writes until reviewed

2. Add Tasks executor behind approval.
   - approved `tasks.insert`
   - idempotency check before write
   - append audit entry

3. Re-auth Keep and add read-only Keep summary.

4. Add Keep read-only summary once OAuth scopes are fixed.

## Design Notes

- Daily brief is not the OS. It is one scheduled report.
- `poll` should update state. `inbox` should display state.
- The approval queue is the safety boundary between read-only intelligence and
  external writes.
- Goose should call MCP tools; launchd should call CLI commands.
