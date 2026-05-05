# Kriya OS Setup Instructions

## Current State
- Repository initialized with AI-nativity (symlinks to AI.md)
- Core stack decisions locked in:
  - Runtime: Goose (Block's MCP-native agent shell)
  - Memory: Mem0
  - Language: Python
  - Daily spend limit: $2.00 USD
  - Phase 1 target: `daily_brief` (read-only summary of calendar, email, finances)
- Security implemented:
  - No .env files or hardcoded secrets
  - All secrets fetched at runtime via `kriya.utils.secrets.get_secret()` using 1Password CLI (`op`)
- 1Password CLI (`op`) confirmed working on system
- Google Workspace CLI (`gws`) and `gws-mcp-server` installed globally via npm

## Remaining Setup Steps (Run in your terminal) - [ALL COMPLETED]

### 1. Authenticate Google Cloud with your personal account [DONE]
### 2. GCP project (REUSING existing: quota was exceeded) [DONE]
### 3. Set up Google Workspace CLI authentication [DONE]
### 4. Verify the setup worked [DONE]
### 5. Install Python dependencies [DONE]

## Goose Configuration
The Goose CLI is configured to use your **Gemini 3.1 Pro** subscription via OAuth. Your configuration is located at `~/.config/goose/config.yaml`.

- **Current Provider:** `gemini_oauth`
- **Current Model:** `gemini-3.1-pro-preview`

To switch between Claude, ChatGPT, or Gemini, edit the `config.yaml` file and uncomment the desired provider block.

## Next Development Steps
Phase 1 is now operational. You can trigger the brief with:
`goose run "get my daily brief"`

## Scheduled Daily Brief
Phase 2 includes a launchd template at:
`launchd/com.savyasachi.kriyaos.daily-brief.plist.template`

Install it with absolute local paths:

```bash
mkdir -p "$HOME/Library/Logs/kriyaos"
sed \
  -e "s#__PYTHON__#$(command -v python3)#g" \
  -e "s#__REPO_PATH__#$(pwd)#g" \
  -e "s#__STDOUT_LOG__#$HOME/Library/Logs/kriyaos/daily-brief.out.log#g" \
  -e "s#__STDERR_LOG__#$HOME/Library/Logs/kriyaos/daily-brief.err.log#g" \
  launchd/com.savyasachi.kriyaos.daily-brief.plist.template \
  > "$HOME/Library/LaunchAgents/com.savyasachi.kriyaos.daily-brief.plist"

launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.savyasachi.kriyaos.daily-brief.plist"
```

The job runs at 7:00 AM local time. `daily_brief` is idempotent and skips if
`state/runs/YYYY-MM-DD-daily_brief.json` already exists.

## Important Notes
- All Python scripts MUST use `kriya.utils.secrets.get_secret()` for secrets
- Never store tokens, keys, or credentials in the repository
- The `state/` directory is for runtime data and is .gitignored
- The daily run aborts when today's `state/usage.jsonl` total reaches `MAX_DAILY_USD` (default: `2.00`)
- Read-only email triage appends grouped unread mail to `state/inbox.md`: `python -m kriya email-triage`
- Pending approval-gated actions can be inspected with `python -m kriya approvals`
- Read-only Google Tasks snapshot writes to `state/tasks-YYYY-MM-DD.md`: `python -m kriya tasks`
- Google Keep needs OAuth re-auth before first use:
  `gws auth login --scopes https://www.googleapis.com/auth/keep.readonly`
- Smoke-test Keep with `gws keep notes list`, then write a snapshot with `python -m kriya notes`
- `python -m kriya poll` updates local state; `python -m kriya inbox` renders local state.
- Run tests with: `python -m unittest discover`

---
Last updated: $(date)
