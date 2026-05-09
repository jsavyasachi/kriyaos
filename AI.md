# kriyaos AI Context

## Stack
- **Runtime:** Goose (Block's open-source MCP-native agent shell)
- **Primary LLM:** Gemini 3.1 Pro (via OAuth subscription)
- **Memory:** Mem0 (bolt-on memory layer)
- **Language:** Python (for MCP servers and glue code)

## Security & Constraints
- **Daily Spend Limit:** $2.00 USD (hard kill-switch per day)
- **Secrets Management:** NO `.env` files. NO hardcoded secrets. All Python scripts MUST fetch secrets at runtime using `kriya.utils.secrets.get_secret("item_name")` which shells out to the 1Password CLI (`op`).
- **OAuth Providers:** Configured in `~/.config/goose/config.yaml` to leverage subscriptions (Claude Pro, ChatGPT Plus, Gemini).

## Roadmap / Phases
- **Phase 1 Target:** `daily_brief` (Read-only summary of calendar, unread emails, and finances). [COMPLETED]
- **Session Handoff:** Read `STATE.md` first. Update it whenever current state, workflow, blockers, completed work, or next plan changes.

## Commands
- **Generate Daily Brief:** `goose run "get my daily brief"`
- **Generate Daily Brief CLI:** `python -m kriya daily-brief`
- **Triage Email CLI:** `python -m kriya email-triage`
- **Tasks Snapshot CLI:** `python -m kriya tasks`
- **Groceries Snapshot CLI:** `python -m kriya groceries`
- **Finance Snapshot CLI:** `python -m kriya finance`
- **Vitals Snapshot CLI:** `python -m kriya vitals`
- **List Pending Approvals:** `python -m kriya approvals`
- **Approve Pending Action:** `python -m kriya approve <id>`
- **Execute Approved Action:** `python -m kriya execute <id>`
- **Reject Pending Action:** `python -m kriya reject <id>`
- **Sync Tasks:** `python -m kriya sync-tasks`
- **Poll OS State:** `python -m kriya poll`
- **Render Inbox:** `python -m kriya inbox`
- **TUI:** `python -m kriya tui`
- **Cost Ceiling Override:** `MAX_DAILY_USD=3.50 python -m kriya daily-brief`
- **Lint:** `uv run --extra dev ruff check .`
- **Test:** `python -m unittest discover`
- **Finance Path Override:** `KRIYA_F5E_REPO=/path/to/f5e python -m kriya finance`
- **Vitals Path Override:** `KRIYA_VITALS_DB=/path/to/health.db python -m kriya vitals`

## MCP Tools
- `daily_brief`
- `email_triage`
- `tasks`
- `groceries`
- `finance`
- `vitals`
- `approvals`
- `approve`
- `execute`
- `reject`
- `sync_tasks`
- `poll`
- `inbox`

## Failure Policy
- Required Google Workspace and Memory integrations fail fast after logging.
- Daily brief treats Memory as optional: broken Mem0 lookup is logged and omitted.
- Finance and vitals remain read-only and render unavailable snapshots when their external data source cannot be read.

## Decisions
- 2026-05-05: next phase scope = approval executor CLI, Keep re-auth + summary, bidirectional Google↔Apple sync, Textual TUI dashboard
- 2026-05-05: Google↔Apple sync is bidirectional, last-write-wins via `state/sync/mappings.json`, with a circuit breaker that aborts when >25 actions are planned in one run
- 2026-05-05: TUI is Textual-based, viewer panes plus an interactive approvals pane (`a`/`r` to approve/reject)
- 2026-05-05: phase sequencing = Slices 1 (executor) and 2 (Keep) in parallel, then 3 (sync), then 4 (TUI)
- 2026-05-05: Google Keep failure is treated as optional (omit on missing scope), mirroring Memory rather than fail-fast Workspace policy
- 2026-05-05: every Google write stays gated by the `state/pending/*.json` approval queue; Apple writes execute inline (local, reversible) but are audited
- 2026-05-05: Apple Calendar writes go through `osascript` since the `ical` CLI is read-only; if brittle, ship Tasks↔Reminders first and defer Calendar sync
- 2026-05-09: Apple Calendar already reads Google calendars via the local Google account; do not add calendar sync unless duplicate-control logic is explicitly designed
- 2026-05-09: Task sync wiring = Google Tasks `To Do` ↔ Apple Reminders list `To do`
- 2026-05-09: Grocery source of truth = Apple Reminders list `Groceries`; Google Keep is unsupported because the Keep OAuth scope is rejected for the current `@gmail.com` OAuth client
- 2026-05-09: Apple Reminders list `Reminders` is Apple-only until the user assigns an external target
- 2026-05-09: Google Keep integration removed; Keep API rejects `keep.readonly` scope on personal `@gmail.com` OAuth clients (Workspace-only), so `notes` CLI/MCP and Keep enrichment in the daily brief were ripped out
- 2026-05-09: TUI is hybrid master/detail with a persistent approvals drawer (left rail = surfaces, right pane = detail)
- 2026-05-09: TUI auto-reloads on filesystem changes via `watchdog`; no LLM-touching auto-poll
- 2026-05-09: TUI is a control surface: `p` triggers `run_poll`, `s` triggers `run_task_sync`, `a`/`r`/`x` act on approvals; long-running ops run in `@work(thread=True, exclusive=True)` workers
- 2026-05-09: TUI supports mouse first-class alongside keyboard (Textual handles natively)
- 2026-05-09: TUI dependencies (`textual`, `watchdog`) live behind a `[tui]` optional-dependencies extra in `pyproject.toml`; core CLI stays light
- 2026-05-09: TUI lives in `kriya/tui/` and is launched via `python -m kriya tui`; no MCP tool exposes it (interactive-only)
