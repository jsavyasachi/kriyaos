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
- **Finance Snapshot CLI:** `python -m kriya finance`
- **Vitals Snapshot CLI:** `python -m kriya vitals`
- **List Pending Approvals:** `python -m kriya approvals`
- **Poll OS State:** `python -m kriya poll`
- **Render Inbox:** `python -m kriya inbox`
- **Cost Ceiling Override:** `MAX_DAILY_USD=3.50 python -m kriya daily-brief`
- **Lint:** `uv run --extra dev ruff check .`
- **Test:** `python -m unittest discover`
- **Finance Path Override:** `KRIYA_F5E_REPO=/path/to/f5e python -m kriya finance`
- **Vitals Path Override:** `KRIYA_VITALS_DB=/path/to/health.db python -m kriya vitals`

## MCP Tools
- `daily_brief`
- `email_triage`
- `tasks`
- `finance`
- `vitals`
- `approvals`
- `poll`
- `inbox`

## Failure Policy
- Required Google Workspace and Memory integrations fail fast after logging.
- Daily brief treats Memory as optional: broken Mem0 lookup is logged and omitted.
- Finance and vitals remain read-only and render unavailable snapshots when their external data source cannot be read.
