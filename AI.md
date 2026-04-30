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

## Commands
- **Generate Daily Brief:** `goose run "get my daily brief"`
