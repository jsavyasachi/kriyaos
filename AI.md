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
- **List Pending Approvals:** `python -m kriya approvals`
- **Poll OS State:** `python -m kriya poll`
- **Render Inbox:** `python -m kriya inbox`
- **Cost Ceiling Override:** `MAX_DAILY_USD=3.50 python -m kriya daily-brief`

## MCP Tools
- `daily_brief`
- `email_triage`
- `tasks`
- `approvals`
- `poll`
- `inbox`
