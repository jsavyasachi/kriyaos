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

## Remaining Setup Steps (Run in your terminal)

### 1. Authenticate Google Cloud with your personal account
```bash
# List your accounts to confirm
/Users/savya/google-cloud-sdk/bin/gcloud auth list

# If not already logged into your personal Gmail:
/Users/savya/google-cloud-sdk/bin/gcloud auth login
# (Choose your personal @gmail.com account in the browser)
```

### 2. Create and configure a dedicated GCP project for Kriya OS
```bash
# Create new project
/Users/savya/google-cloud-sdk/bin/gcloud projects create kriya-os --name="Kriya OS"

# Set as active project
/Users/savya/google-cloud-sdk/bin/gcloud config set project kriya-os

# Verify
/Users/savya/google-cloud-sdk/bin/gcloud config get-value project
# Should output: kriya-os
```

### 3. Set up Google Workspace CLI authentication
```bash
# This will:
#   - Create OAuth credentials in the kriya-os project
#   - Enable required APIs (Gmail, Calendar, etc.)
#   - Perform the final OAuth consent flow in your browser
gws auth setup --login
```

### 4. Verify the setup worked
```bash
# Check authentication status
gws auth status

# Test a simple read-only command (should show your profile)
gws gmail users get --params '{"userId":"me"}'
```

### 5. Install Python dependencies (as needed)
```bash
# For Mem0 integration
pip install mem0ai

# For any additional MCP servers or tools
# pip install <package>
```

## Next Development Steps
Once the above is complete, you can begin implementing:
1. The `daily_brief.py` script that will:
   - Fetch secrets via `kriya.utils.secrets.get_secret()`
   - Use `gws` to get calendar events and unread emails
   - Use your existing `f5e` project to get financial summary
   - Write the brief to `state/daily-brief-YYYY-MM-DD.md`
2. Wrap this script as a Goose extension or MCP server
3. Configure Goose to run it on a schedule (via launchd or similar)

## Important Notes
- All Python scripts MUST use `kriya.utils.secrets.get_secret()` for secrets
- Never store tokens, keys, or credentials in the repository
- The `state/` directory is for runtime data and is .gitignored
- Run tests with: `python -m unittest discover`

---
Last updated: $(date)