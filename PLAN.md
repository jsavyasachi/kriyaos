# Review of `megaplan.md` (Gemini "Personal AI OS" plan) + Enhanced Plan

> Audience: another AI continuing this work after the current Claude Code session ends. Self-contained: read this top to bottom. All factual claims about the 2026 ecosystem are cited inline; verify before acting on them.

---

## Context

`/Users/savya/projects/ai-dotfiles/megaplan.md` is a 2-turn chat with Gemini CLI in which the user asked how to build an "AI secretary" / personal OS that reads email, manages calendar, reviews finances, eventually runs autonomously on cron. Gemini proposed:

1. **New repo** `<repo>` (separate from `ai-dotfiles`).
2. **Phased UI**: terminal chat → TUI (Ink/Textual) → Next.js dashboard.
3. **MCP everywhere**: email, calendar, finance (`f5e`), system as separate MCP servers.
4. **LangGraph** as the orchestration kernel.
5. **Memory** via Chroma / SQLite-embeddings or reuse `lorekeeper`.
6. **Phased buildout**: read-only loop → cron daemon → dashboard.
7. Cited inspirations: AIOS (agiresearch), Open Interpreter, CrewAI, AutoGen, Agent Zero, PAI (Miessler).

Direction is sound. **But the plan has significant holes, missed tooling, and zero security model.** This doc enumerates them, then gives an enhanced plan.

User's existing assets relevant to this build:
- `~/projects/ai-dotfiles` - cross-agent config (Claude Code + OpenCode + Gemini CLI), skills/, hooks/, commands/, memory/. Already has the "AI Nativity" symlink rule.
- `~/projects/f5e` - Kotak/Zerodha finance scraper + analyzer (Python).
- `~/projects/{vitals, folio, mac-battery-cycle-history, SampleChain}` - peripheral.
- 1Password CLI (`op`) installed and authed via Touch ID - currently unused by megaplan.

---

## Holes in Gemini's plan

### H1. Reinventing tooling that already exists

Gemini said: *"You can create an `email-mcp` or `calendar-mcp`."*

**Don't.** Use [`googleworkspace/cli`](https://github.com/googleworkspace/cli) (`gws`) - maintained under the `googleworkspace` GitHub org (25K+ stars). It self-discloses *"not officially supported"* but is the canonical agent-friendly Workspace surface, far better than random community MCPs. It covers **Gmail, Calendar, Drive, Sheets, Docs, Chat, Admin** in one binary, with:

- **Structured JSON output** on every command (no scraping needed).
- **100+ pre-built agent skills** (SKILL.md files) for triage, send, reply, agenda, event creation, etc.
- A **Gemini CLI extension** (so it slots into the user's existing Gemini CLI setup natively).
- Integrations with OpenClaw and other agent frameworks.

Wrap `gws` calls in a thin local MCP server (or use it directly as a tool from Claude Agent SDK: no MCP needed if the agent can shell out). Either way, you skip the entire "design OAuth, refresh tokens, build resource handlers" subproject.

There is also Google's announced [official remote MCP for Workspace/Cloud services](https://cloud.google.com/blog/products/ai-machine-learning/announcing-official-mcp-support-for-google-services): keep an eye on it, but as of Q1 2026 the consumer-side coverage is unclear; `gws` is the pragmatic pick now.

**Action:** Drop the "build email-mcp/calendar-mcp" tasks entirely. Install `gws`, OAuth it once, expose it to the agent. Read-only scopes first.

### H2. Missed: Goose (the most relevant existing project)

Gemini surveyed Open Interpreter, CrewAI, AutoGen, LangGraph, Agent Zero - but **never mentioned Goose** by Block, despite it being the closest pre-built thing to what the user is describing. ([Goose docs](https://goose-docs.ai/), [Block's announcement](https://block.xyz/inside/block-open-source-introduces-codename-goose), [Top 10 open-source local agents 2026](https://fast.io/resources/top-10-open-source-ai-agents/))

Goose:
- Native macOS desktop app + CLI + API. Rust core.
- **MCP-native**: Block co-designed MCP with Anthropic, so all the "tooling layer" Gemini wants is just `goose` extensions.
- 15+ LLM providers (Anthropic, OpenAI, Google, Ollama, OpenRouter, Bedrock).
- Has **scheduling** (cron-style recipes) and **sub-agent** spawning built in.
- Apache 2.0; recently moved to Linux Foundation's Agentic AI Foundation (AAIF).

This isn't a tangential mention: Goose may **already be the "Phase 1+2" runtime** Gemini is asking the user to build from scratch. Skipping it costs the user weeks.

**Action:** Evaluate Goose as the runtime shell before committing to "build from scratch on LangGraph." Even if you reject it, the rejection should be conscious.

### H3. Missed: Claude Agent SDK (the user's natural fit)

The user is a heavy Claude Code user (`ai-dotfiles` is built around it). Anthropic renamed the Claude Code SDK to **Claude Agent SDK** alongside Claude 4.6: same engine that powers Claude Code, but for general agent loops, not just coding. ([2026 framework showdown - QubitTool](https://qubittool.com/blog/ai-agent-framework-comparison-2026))

For someone whose entire workflow is already in Claude Code, the Agent SDK is the **lowest-friction path** to a personal OS: you reuse skills/, hooks/, commands/ that already exist in `ai-dotfiles` rather than learning LangGraph state-machine syntax.

This is exactly the bet **PAI (Daniel Miessler)** made: see H4.

**Action:** Add Claude Agent SDK to the runtime shortlist. It is the natural choice given the user's investment in Claude Code primitives.

### H4. PAI was named-dropped but not actually evaluated

Gemini cited PAI as inspiration but didn't recognize that **PAI v2.0 (released 2025-12-28) is essentially the architecture being proposed**, already built and maintained, on top of Claude Code. ([github.com/danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure), [PAI blog post](https://danielmiessler.com/blog/personal-ai-infrastructure))

PAI provides: skills (modular capabilities), persistent memory, intelligent routing, "self-improvement" loops - all on Claude Code primitives. There's even a community OpenCode port ([Steffen025/pai-opencode](https://github.com/Steffen025/pai-opencode)) which matters because the user runs OpenCode too.

**Action:** Spend 30 min reading PAI's repo and decide: fork it, take ideas from it, or roll your own. Don't ignore it.

### H5. Memory layer is hand-wavy: Letta exists for exactly this

Gemini said: *"vector database (like Chroma or local SQLite with embeddings) OR your existing Lorekeeper"*

This conflates two different things: RAG-style retrieval (Chroma) vs. agent-managed OS-style memory. For a "Personal OS" the latter is a much better fit. **Letta (formerly MemGPT)** treats agent memory as an OS: core memory (RAM), archival memory (disk), recall memory (history) - the agent decides what to keep close vs. archive. ([github.com/letta-ai/letta](https://github.com/letta-ai/letta), [Hermes OS comparison](https://hermesos.cloud/blog/ai-agent-memory-systems), [vectorize.io Mem0 vs Letta](https://vectorize.io/articles/mem0-vs-letta))

Alternatives: **Mem0** (lightweight memory layer that bolts onto any framework), **LangMem SDK** (if you go LangGraph).

**Action:** Pick one of {Letta, Mem0, LangMem} for agent memory. `lorekeeper` is a public repo: personal facts must never go there. Mem0 covers both use cases.

### H6. ZERO security model: biggest hole

For a system with Gmail send, calendar write, and finance access running on cron, Gemini wrote nothing about:

- **Secrets management.** User has 1Password CLI (`op`) installed and authed via Touch ID - already documented in `~/.claude/CLAUDE.md`. **None of the megaplan uses it.** OAuth tokens, API keys, anything sensitive should live in 1Password and be fetched via `op item get --fields ... --reveal`. Anthropic + 1Password also have a tighter integration story now ([1Password Unified Access](https://1password.com/press/2026/mar/1password-unified-access)).
- **OAuth scopes.** Default to read-only (`gmail.readonly`, `calendar.readonly`). Send/write scopes only when explicitly enabled per-skill.
- **Approval gates / human-in-the-loop.** An autonomous loop that can `send_email` is one prompt-injection away from disaster. Any *write* action must hit an approval queue (`inbox.md` / SQLite table) and require explicit user confirmation before execution. Gemini's draft has the agent doing irreversible actions on cron with no gate.
- **Idempotency.** Cron + LLM = duplicate sends if you're not careful. Every write tool needs an idempotency key (e.g., hash of `{thread_id, intent, day}`) and a dedup table.
- **Audit log.** Append-only log of `(timestamp, tool, args, result)` for every tool call. Non-negotiable for a system this autonomous.
- **Prompt-injection containment.** Email bodies are **untrusted input**. Any planner that sees raw email content and also has `send_email` access is a security hole. Architect the planner so write tools are gated by a separate confirmer that does NOT read untrusted input.
- **Sandboxing.** Gemini mentioned Docker/E2B once and never integrated it. Local code-execution tools (shell, python) must run in a container or strictly constrained subprocess.

**Action:** A "Security & Trust" section is mandatory in the real plan. See enhanced plan §4.

### H7. No MCP gateway: multiple MCPs without one is messy

User will end up with ≥4 MCP servers (Gmail, Calendar, f5e, system). Connecting each directly to the agent multiplies auth surface, name collisions, and observability gaps. **MCP gateways** (reverse proxies in front of N MCP servers) are the 2026 best practice: they centralize auth, namespace tools (`gmail.send`, `cal.create`), and provide a single audit point. ([5 best MCP gateways 2026 - TrueFoundry](https://www.truefoundry.com/blog/best-mcp-gateways), [MCP gateway patterns - ChatForest](https://chatforest.com/guides/mcp-gateway-proxy-patterns/), [Q1 2026 ecosystem state - heyitworks.tech](https://www.heyitworks.tech/blog/mcp-aggregation-gateway-proxy-tools-q1-2026))

Options: `mcp-gateway` (Microsoft sample), Obot, Composio, MintMCP. Self-hosted local gateway is enough - no need for enterprise tier.

**Action:** Plan for a thin local MCP gateway from day one. Even if it's just `mcp-proxy`-style aggregation.

### H8. AIOS reality-check

Gemini cited AIOS (agiresearch/AIOS) as a "Key Project" but it's a **research project: ~5.1K stars, ~27 contributors, COLM 2025 paper, no production deployments**. ([github.com/agiresearch/AIOS](https://github.com/agiresearch/AIOS)) Fine as inspiration, dangerous as a dependency. Make sure the next AI/dev doesn't try to use it as infrastructure.

### H9. UI roadmap stacks three different runtimes

Gemini's progression: terminal → Ink (Node/React) → Textual (Python) → Next.js. That's three runtimes for the UI alone, and it doesn't even include the orchestration runtime. **Pick one language and one UI stack.** Whatever the orchestration runtime is, the dashboard should match (Node-based core → Next.js dashboard; Python core → Textual or FastAPI+HTMX).

**Action:** Lock language choice up front (see Open Question OQ-1).

### H10. Cost & failure modes ignored

A `while True` LLM loop on cron, even hourly, racks up real money fast (full context every poll). And no plan for: timeouts, partial failures, retry policy, dead-letter queue, backoff. Production-grade autonomy needs all of these.

**Action:** Set a hard daily $ ceiling (e.g., `MAX_DAILY_USD=2.00`) checked before each loop. Skip the loop if exceeded. Log every call's token usage.

### H11. LangGraph TS recommendation: verified, but caveat

Gemini's specific suggestion to use **LangGraph (TypeScript)** does hold up. As of April 2026, `@langchain/langgraph` has ~42K weekly npm downloads and is used in production by Uber, LinkedIn, Replit, GitLab. ([LangGraph TS guide](https://langgraphjs.guide/), [framework hub](https://www.agentframeworkhub.com/blog/langgraph-news-updates-2026)) So if the runtime decision lands on "build it custom," LangGraph TS is fine.

But: LangGraph is a *workflow engine*, not a personal-OS. It gives you state machines and checkpointing, nothing more. The "OS" still has to be built. This is why H2/H3 (Goose, Claude Agent SDK) matter: they're closer to "shell + skills" out of the box.

### H12. The "AI Nativity" rule from `ai-dotfiles` is not applied

Gemini said "Make sure it's AI Native!" but didn't lay out the actual symlink commands or skills/hooks/commands directory layout, even though those are explicitly defined in the user's own `~/.claude/CLAUDE.md`. The next AI should follow the rule literally:

```
mkdir <repo> && cd <repo>
git init
# Write project-specific instructions to AI.md, then:
ln -s AI.md CLAUDE.md
ln -s AI.md OPENCODE.md
ln -s AI.md GEMINI.md
```

---

## Enhanced Plan

### 0. Decisions to make BEFORE any code

These three choices are the load-bearing ones. Get them wrong and everything else is rework.

| Decision | Options | Default recommendation |
|---|---|---|
| **OQ-1 Runtime shell** | (a) Goose as base, extend via MCPs+recipes; (b) Claude Agent SDK + skills/hooks (PAI-style); (c) Build custom on LangGraph TS | (b) Claude Agent SDK - lowest friction given the user's existing Claude Code investment, plus PAI v2 already shows the pattern works. Fall back to (a) Goose if you want a battle-tested runtime with desktop UI for free. Avoid (c) unless you have specific reason to control everything. |
| **OQ-2 Memory layer** | (a) Letta (OS-style); (b) Mem0 (lightweight overlay); (c) LangMem (only if (c) above) | (b) Mem0 for v1 - minimal lift, agent-framework-agnostic. Migrate to (a) Letta if memory becomes the bottleneck. `lorekeeper` is **not** a memory layer; it's a knowledge tool the agent queries. |
| **OQ-3 Repo strategy** | (a) New repo (name TBD by user); (b) Fork PAI; (c) Subdir of `ai-dotfiles` | (a) **New repo**, AI-Native (symlinks per `ai-dotfiles` rule). Steal liberally from PAI's skill structure but don't fork - PAI is opinionated and the user's setup has its own conventions. **Name: user's call** - Gemini's `personal-os` suggestion was rejected. Candidates worth surfacing: `aide`, `concierge`, `homunculus`, `kernel`, `sidekick`, `executive`, `daemon`, `me-os`, `system-one`. Don't pick one yourself; ask. |

The next AI: confirm these three with the user before writing code. Use the [`AskUserQuestion`] tool if available, otherwise present as a numbered list and stop.

### 1. Architecture (target state)

```
┌──────────────────────────────────────────────────────────┐
│                    User Surfaces                         │
│  CLI (Claude Code session)  │  Web dashboard (Next.js)   │
│       triggers/queries      │   approve queue, summary   │
└──────────────┬───────────────────────────┬───────────────┘
               │                           │
               ▼                           ▼
        ┌────────────────────────────────────────┐
        │   Orchestrator (Claude Agent SDK)      │
        │   - Skills (read_email, plan_day, …)   │
        │   - Approval gate before any *write*   │
        │   - Audit log + idempotency dedup      │
        │   - Daily $ ceiling check              │
        └─────────────┬───────────────────┬──────┘
                      │                   │
              ┌───────▼─────────┐   ┌─────▼──────────┐
              │  Memory (Mem0)  │   │  Tool Layer    │
              │                 │   │ (gws + MCPs    │
              │                 │   │  via gateway)  │
              └─────────────────┘   └─┬─────────┬───┘
                                      │         │
                                      ▼         ▼
                              googleworkspace  f5e
                                /cli (gws)    (MCP or
                              Gmail+Cal+Drive  skill)
                                  ▲
                                  │ OAuth tokens via `op`
                                  ▼
                               1Password
```

### 2. Phased buildout (revised)

#### Phase 0 - Foundation (day 1, ~2h)
1. Create `~/projects/<repo>`, `git init`.
2. Write `AI.md` with: stack, run commands, layout, approval gate rules, scope-of-trust statement.
3. `ln -s AI.md CLAUDE.md && ln -s AI.md OPENCODE.md && ln -s AI.md GEMINI.md`.
4. Add `README.md` with the `## Stack` badge block (per `~/.claude/CLAUDE.md` rule).
5. Add `.gitignore` covering `.env`, `*.db`, `secrets/`, `state/`, `node_modules/`, `.venv/`.
6. Choose runtime per OQ-1; install minimal deps; commit (Conventional Commits: `chore: init repo`).

#### Phase 1 - Read-only daily brief (week 1)
**Goal:** at 7am, agent prints/writes a daily brief: today's calendar + flagged unread emails + finance summary. **No writes to the outside world.**

1. Install [`gws`](https://github.com/googleworkspace/cli). Run its OAuth flow once; persist tokens to a 1Password item via `op item create`. Boot wrapper fetches token via `op item get --fields … --reveal` and writes it to the path `gws` expects, then unsets it.
2. Read-only first: only request `gmail.readonly` and `calendar.readonly` scopes during the OAuth dance. `gws` exposes Gmail/Calendar via JSON-out commands; the agent invokes them as tools (no separate MCP server needed if the runtime can shell out; otherwise put a thin MCP wrapper around `gws` and put it behind a local **MCP gateway** - `mcp-proxy` or Microsoft's `mcp-gateway` sample is enough).
3. Wire `f5e` as an MCP server (or as a Claude Code skill) exposing `summarize_finances`.
4. Create skill `daily_brief` that calls the three and writes `state/daily-brief-YYYY-MM-DD.md`.
5. Run manually first. Verify output.
6. Add **audit log** (`state/audit.jsonl`) - every tool call appended, no exceptions.

#### Phase 2 - Cron / scheduled polling (week 2)
**Still read-only. Still no autonomous writes.**

1. Wrap `daily_brief` in a launchd plist (macOS-native; better than cron for laptops that sleep). Trigger: 7am local; `RunAtLoad=false`.
2. Add **idempotency**: skill writes `state/runs/{date}-{skill}.json`; if present, skip.
3. Add **cost ceiling**: `state/usage.jsonl` aggregated daily; skill aborts if today's spend > `MAX_DAILY_USD`.
4. Add **failure handling**: try/catch around every tool call, errors → `state/errors.jsonl`, surface in tomorrow's brief.
5. Add second skill: `email_triage` - classifies unread emails as {urgent, normal, newsletter, automated} and appends to `state/inbox.md`. Read-only - no archiving, no replies.
6. Add Google Tasks read-only summary to daily brief and `state/tasks-YYYY-MM-DD.md`; later promote approved email action items into Tasks via approval queue.
7. Google Keep is supported by `gws`, but current OAuth token lacks Keep scopes. Re-run `gws` auth with `https://www.googleapis.com/auth/keep.readonly`, then add read-only Keep note summary/capture review.

#### Phase 3 - Approval-gated writes (week 3-4)
**This is where it gets dangerous. Be careful.**

1. Introduce **approval queue**: `state/pending/{id}.json` for any proposed write action. Each item: `{tool, args, rationale, idempotency_key, expires_at}`. [FOUNDATION ADDED: deterministic local queue only; no executor yet.]
2. Build a TUI or simple Web UI (matching runtime - Next.js if Node-based core) that lists pending items and offers `approve | reject | edit`.
3. Add a **separate "executor"** process - runs only when invoked by approval action; takes the approved item and calls the underlying MCP tool. Executor has **no LLM** in its loop. It's deterministic. This is the prompt-injection containment from H6.
4. Enable **write tools one at a time, behind feature flags**: start with `calendar.create_event` (low blast radius, easily reversed). Then `gmail.draft` (creates a draft, doesn't send). Only much later - `gmail.send`.
5. Every write tool requires: scope upgrade in OAuth, approval-queue gating, idempotency key, audit log entry.

#### Phase 4 - Memory + cross-skill context (week 4+)
1. Stand up Mem0 (or chosen memory layer). Persist across runs.
2. Add long-term memories: people, recurring meetings, financial accounts, preferences.
3. Mem0 handles both explicit knowledge (named facts) and implicit recall - no separate knowledge store needed.

#### Phase 5 - Dashboard (week 6+)
1. Next.js (if Node) / FastAPI+HTMX (if Python) reading `state/`.
2. Views: today's brief, approval queue, audit log, cost-to-date, agent's current memory snapshot.
3. Auth: localhost-bound only. No public-facing surface, ever.

### 3. Files to read before starting

- `/Users/savya/.claude/CLAUDE.md` - global rules (commits, READMEs, AI Nativity, `op` usage).
- `/Users/savya/projects/ai-dotfiles/instructions/AI.md` - same content, repo-local copy.
- `/Users/savya/projects/ai-dotfiles/extensions/skills/` - existing skills, pattern reference.
- `/Users/savya/projects/ai-dotfiles/extensions/hooks/` - hook patterns.
- `/Users/savya/projects/f5e/AI.md` - to know what `f5e` exposes.
- `https://github.com/danielmiessler/Personal_AI_Infrastructure` - PAI v2 README and Releases.
- `https://goose-docs.ai/` - if OQ-1 lands on Goose.

### 4. Security checklist (must-pass before any phase ships)

- [ ] No secrets in code, `.env`, or git history. All via `op item get --fields … --reveal`.
- [ ] OAuth scopes are minimum-necessary. Read-only first; writes only with explicit per-tool feature flag.
- [ ] Approval queue exists before any write tool is registered with the LLM.
- [ ] Executor for approved actions has **no LLM** in its loop.
- [ ] Idempotency key on every write tool; dedup table consulted before exec.
- [ ] Audit log is append-only and rotated daily.
- [ ] Daily $ ceiling check before each scheduled run.
- [ ] Local code-exec tools (shell/python) run in container or constrained subprocess. Default = disabled.
- [ ] Email-body content is never passed to a planner that has write-tool access. Two-stage planner→confirmer pattern, or strip-and-summarize before exposing to write-capable agent.
- [ ] Dashboard binds to `127.0.0.1` only.

### 5. Verification (end-to-end test plan)

After each phase, you should be able to:

**Phase 1:** Run `<repo> run daily_brief` from terminal. See `state/daily-brief-{today}.md` populated with calendar + email summary + f5e numbers. Audit log has N entries matching the tool calls.

**Phase 2:** Disable Mac sleep, leave laptop running, check next morning that brief was generated at 7am, no duplicate entries even if you trigger manually too. Check `state/usage.jsonl` shows yesterday's cost.

**Phase 3:** Trigger `email_triage` with an email that suggests a calendar event. Verify a `state/pending/*.json` appears, NOT a calendar entry. Approve via UI. Verify executor creates the event. Try replaying the same approval - verify idempotency rejects.

**Phase 4:** Tell the agent "I prefer morning meetings." Restart the process. Ask it to schedule something - confirm preference is recalled.

**Phase 5:** Open localhost dashboard. Confirm only-localhost-listening (`netstat -an | grep LISTEN | grep .3000.` shows `127.0.0.1:3000`, not `*:3000`).

### 6. What to drop from Gemini's plan

- "Build email-mcp/calendar-mcp from scratch" - use [`googleworkspace/cli`](https://github.com/googleworkspace/cli) (`gws`) instead. One binary, structured JSON, 100+ agent skills, Gemini CLI extension. Wraps Gmail+Calendar+Drive+Sheets+Docs+Chat+Admin.
- AIOS as anything but inspiration - it's research, not infra.
- Three-runtime UI roadmap (Ink + Textual + Next.js) - pick one, matching core.
- Chroma/SQLite-embeddings as memory - use Mem0 or Letta.
- "It's just a cron job" framing - needs idempotency, ceilings, audit, approval gates.

### 7. What to keep from Gemini's plan

- New repo, separate from `ai-dotfiles` - correct call.
- MCP-everywhere as the tool layer - correct, just don't roll your own where official exists.
- Phased read-only-first buildout - correct instinct, just add the security gates.
- LangGraph TS (if going custom path) - verified production-mature in 2026.
- f5e and lorekeeper integration - correct, just clarify lorekeeper = tool, not memory.

### 8. Open questions to confirm with user before coding

1. **OQ-1 runtime shell** - Claude Agent SDK (recommended), Goose, or LangGraph-custom?
2. **OQ-2 memory layer** - Mem0 (recommended), Letta, or LangMem?
3. **OQ-3 repo strategy** - new `<repo>` (recommended), fork PAI, or subdir of `ai-dotfiles`?
4. **Language** - TS/Node (matches lorekeeper, recommended if Claude Agent SDK or LangGraph) or Python (matches f5e)?
5. **Daily cost ceiling** - what dollar amount per day is the kill-switch? Default proposal: $2/day.
6. **First-skill scope** - start with `daily_brief` (recommended) or something more ambitious?

---

## Sources (validation)

- PAI: [github.com/danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure), [danielmiessler.com PAI blog](https://danielmiessler.com/blog/personal-ai-infrastructure)
- Official Google MCP: [Google Cloud Blog announcement](https://cloud.google.com/blog/products/ai-machine-learning/announcing-official-mcp-support-for-google-services)
- Goose: [goose-docs.ai](https://goose-docs.ai/), [Block announcement](https://block.xyz/inside/block-open-source-introduces-codename-goose)
- Claude Agent SDK: [QubitTool 2026 framework comparison](https://qubittool.com/blog/ai-agent-framework-comparison-2026)
- Letta vs Mem0 vs LangMem: [Hermes OS dual-layer memory](https://hermesos.cloud/blog/ai-agent-memory-systems), [Mem0 vs Letta - Vectorize](https://vectorize.io/articles/mem0-vs-letta), [github.com/letta-ai/letta](https://github.com/letta-ai/letta)
- AIOS reality: [github.com/agiresearch/AIOS](https://github.com/agiresearch/AIOS)
- LangGraph TS maturity: [langgraphjs.guide](https://langgraphjs.guide/), [agentframeworkhub.com](https://www.agentframeworkhub.com/blog/langgraph-news-updates-2026)
- MCP gateways: [TrueFoundry top 5](https://www.truefoundry.com/blog/best-mcp-gateways), [ChatForest patterns guide](https://chatforest.com/guides/mcp-gateway-proxy-patterns/), [Q1 2026 ecosystem state](https://www.heyitworks.tech/blog/mcp-aggregation-gateway-proxy-tools-q1-2026)
- 1Password for agents: [1Password Unified Access press release Mar 2026](https://1password.com/press/2026/mar/1password-unified-access)

**Confidence: 88%** | sources cited inline above. Lower than 95% because: (a) ecosystem is moving fast, double-check Goose's recipe-scheduling capability and whether Google's official MCP covers personal Gmail (not just Workspace) before committing; (b) the "executor with no LLM" pattern is a defensive choice: if you need LLM-driven write decisions, the design needs more thought than this plan provides.
