# 🤖 auto-agent

> A platform-agnostic multi-agent framework for software engineering — using specialized smaller models working together to plan, code, and review better than a single large model, at a fraction of the cost.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform: OpenCode](https://img.shields.io/badge/Platform-OpenCode-blue.svg)](https://opencode.ai)
[![Models: OpenCode Go](https://img.shields.io/badge/Models-OpenCode%20Go-green.svg)](https://opencode.ai)

---

## 💡 The Insight

Most developers point a single powerful model (Claude Opus, GPT-4o) at every task. This works — but it's expensive, slow, and the model has no checks on itself.

This framework takes a different approach:

```
❌ One model does everything
✅ Specialized agents, each doing one job well
```

Three specialized agents, each with a clear role, checking each other's work:

```
🧠 Planner  →  💻 Coder  →  🔍 Reviewer  +  ✅ Approver
```

The result: **better quality, built-in guardrails, and significantly lower cost.**

---

## 🏗️ Architecture

```
Your task
    ↓
🔍 PRE-FLIGHT — git status auto-checked and injected into planner context
    ↓
🧠 PLANNER — breaks task into clear steps (aware of unpushed/uncommitted state)
    ↓
[Human reviews the plan — approves or rejects]
    ↓
💻 CODER — implements exactly the plan, commits, pushes
    ↓
🔍 REVIEWER  +  ✅ APPROVER — two independent verdicts
    ↓
Both APPROVED       → ✅ pull to your server
Both CHANGES NEEDED → ❌ auto-loops back to coder (max 3 retries)
Split verdict       → ⚠️  you decide
```

### Smart Routing

The planner intelligently routes tasks to the right agent:

| Route | When | Flow |
|-------|------|------|
| `[ROUTE: coder]` | Feature, fix, or bug | Planner → Coder → Reviewer + Approver |
| `[ROUTE: reviewer]` | Check a commit | Reviewer + Approver only |
| `[ROUTE: none]` | General question | Planner answers directly |

---

## ✨ Key Features

### 1. Git Pre-Flight Check
Before the planner even sees your task, the orchestrator automatically checks your git state and injects it as context:
- Current branch
- Any unpushed commits
- Any uncommitted changes

This means the planner always knows your repo's state without you having to describe it. If you have uncommitted changes or unpushed commits, it factors that into the plan automatically.

### 2. Role Boundaries with Intent Detection
Each agent detects when it's being asked to do the wrong job and redirects:
```
User asks coder: "I have a problem, not sure what to do"
Coder responds: "❌ Planning is not my job. Please switch to the planner agent."
```

### 3. Human Approval Gate
After planning, the pipeline pauses for your review before any code is written:
```
⚠️  HUMAN APPROVAL REQUIRED
Review the plan above carefully.
Proceed? (yes/y or no/n):
```

### 4. Two-Agent Consensus Review
Every commit goes through two completely independent agents before any verdict is issued:
- **Reviewer (GLM-5)** — first pass: bugs, logic errors, security, code quality
- **Approver (MiniMax M2.7)** — independent second opinion, does not see the reviewer's verdict

Three possible outcomes:
- Both approve → ✅ deploy
- Both reject → ❌ auto-route back to coder
- Split verdict → ⚠️ you decide

### 5. Auto Retry Loop
If the reviewer rejects, the orchestrator automatically routes back to the coder with the issues — no manual intervention needed. Up to 3 retries before escalating to you.

### 6. Cost Efficient
Uses [OpenCode Go](https://opencode.ai) models — **$5 for your first month, then $10/month** for all three models:

| Agent | Model | Monthly Requests |
|-------|-------|-----------------|
| Planner | Kimi K2.5 | ~9,250 |
| Coder | MiniMax M2.5 | ~100,000 |
| Reviewer | GLM-5 | ~5,750 |
| Approver | MiniMax M2.7 | ~5,750 |

> **Compare this to:** Claude Opus or GPT-4o at $15–$30 per million tokens with no usage ceiling built in. OpenCode Go gives you predictable flat-rate pricing with generous limits.

---

## 💰 OpenCode Go Pricing & Limits

This framework is designed to run on [OpenCode Go](https://opencode.ai) — a low cost subscription giving reliable access to curated open coding models.

| Plan | Cost |
|------|------|
| First month | $5 |
| Monthly thereafter | $10 |

### Usage Limits per Billing Period

| Limit | Value |
|-------|-------|
| Per 5 hours | $12 of usage |
| Per week | $30 of usage |
| Per month | $60 of usage |

### Estimated Requests per Month

| Model | Requests/month |
|-------|---------------|
| GLM-5 | ~5,750 |
| Kimi K2.5 | ~9,250 |
| MiniMax M2.5 | ~100,000 |

> Note: If you reach usage limits, OpenCode falls back to free models automatically. You can also enable balance top-up in the OpenCode console.

---

## 🔀 Two Ways to Use This Framework

There are two distinct modes — pick the right one for the job.

---

### Mode 1 — Automated Pipeline (CLI function)

```bash
myapp add a user authentication feature
# or with quotes — both work
myapp "add a user authentication feature"
```

Best for **autonomous software engineering**. You fire off a task, the agents handle planning, coding, and reviewing end-to-end with auto-routing — minimal interaction needed.

✅ Use this for:
- Building new features
- Fixing bugs
- Reviewing commits before deployment
- Refactoring code

❌ Not suited for:
- Back-and-forth discussions or exploratory questions
- Tasks where you want to guide the agent step by step
- Anything requiring mid-flow human interaction

---

### Mode 2 — Manual Agents via OpenCode TUI (Tab menu)

Open OpenCode in your terminal and press `Tab` to switch between agents manually:

```
opencode          ← launch the TUI
Tab               ← cycle through: Planner / Coder / Reviewer
```

This gives you a **full chatbot experience** — you can talk to each agent conversationally, ask follow-up questions, explore options, and guide the work yourself.

✅ Use this for:
- Discussing architecture or design decisions
- Exploratory debugging where you're not sure what the fix is
- Step-by-step guidance where you want to stay in control
- Any interactive Q&A with your codebase

---

> **Rule of thumb:** Know exactly what you want built or fixed? → Use the CLI function. Want to think it through with an agent first? → Use the TUI.

---

## 🚀 Quick Start

### Prerequisites
- [OpenCode CLI](https://opencode.ai) installed
- [OpenCode Go subscription](https://opencode.ai) ($5 first month, $10/month)
- Python 3.8+

### Installation

**1. Clone the repo**
```bash
git clone https://github.com/sanprat/auto-agent.git
cd auto-agent
```

**2. Copy agent files to your project**
```bash
mkdir -p your-project/.opencode/agents
cp opencode/agents/* your-project/.opencode/agents/
cp opencode/opencode.json your-project/.opencode/
cp opencode/orchestrator.py your-project/.opencode/
```

**3. Connect OpenCode Go**
```bash
# Inside OpenCode TUI
/connect → select OpenCode Go → paste your API key
```

**4. Update the project path in orchestrator.py**
```python
# Line 20 in orchestrator.py
PROJECT_DIR = "/path/to/your/project"
```

**5. Add a shell function**

Open `~/.zshrc` (or `~/.bashrc` if you use bash) and add this function — replace `myapp` with your project name and update the path:

```bash
# Add to ~/.zshrc or ~/.bashrc
function myapp() {
  python /path/to/your-project/.opencode/orchestrator.py "$*"
}
```

Then reload your shell:
```bash
source ~/.zshrc
```

> 💡 **Why a function instead of an alias?** A shell function with `"$*"` collects everything you type after `myapp` as a single string — so you don't need to wrap your prompt in quotes. Both work, but the function is more convenient for natural language tasks.

**6. Run!**

With the function, you can type naturally — no quotes needed:
```bash
myapp add a user authentication feature
```

Or with quotes if you prefer — both work:
```bash
myapp "add a user authentication feature"
```

---

## 🧠 How to Use — Writing Good Prompts

This is a **fire-and-forget pipeline**, not a chat assistant. The prompt you pass in is the only instruction the agents receive — so make it count.

### Syntax

```bash
# Without quotes (recommended — more natural to type)
myapp add a stop loss feature to the trading engine

# With quotes (also fine)
myapp "add a stop loss feature to the trading engine"
```

Replace `myapp` with whatever function name you set up. Thanks to the `"$*"` in the shell function, both styles work identically.

### Prompt Formula

```
[action verb]  +  [specific thing]  +  [optional: file or context]
```

| Part | Examples |
|------|---------|
| Action verb | `add`, `fix`, `refactor`, `review`, `remove`, `update` |
| Specific thing | feature name, error message, function name, file path |
| Optional context | `in api/broker.py`, `on the dashboard`, `before deploying` |

---

### ✅ Good Prompts

```bash
# Feature work
myapp "add stop loss logic to the order execution module"
myapp "add a trailing stop feature with configurable percentage"
myapp "implement position sizing based on account balance"

# Bug fixes
myapp "fix the KeyError crash in strategy/momentum.py when volume data is missing"
myapp "fix the race condition in the order queue when two signals fire simultaneously"

# Refactoring
myapp "refactor the broker connection logic into a dedicated BrokerClient class"
myapp "extract the indicator calculations from main.py into a separate indicators module"

# Code review
myapp "review the latest commit before deploying to production"
myapp "review the risk management changes in the last 3 commits"

# General questions (answered by planner directly, no code written)
myapp "do I need to rebuild the docker container after pulling the latest changes?"
myapp "what's the best way to handle WebSocket reconnections in this codebase?"
```

### ❌ Bad Prompts

```bash
# Too vague — agents can't act on these
myapp "help me"
myapp "something is broken"
myapp "check my code"
myapp "review everything"
myapp "make it better"

# Wrong tool — use OpenCode TUI directly for these
myapp "can we chat about architecture options?"   # → use TUI interactively
myapp "what's the server CPU usage?"              # → check your server directly
myapp "show me the latest trade logs"             # → query your DB directly
```

---

### 🔀 How Routing Works

The planner reads your prompt and decides which pipeline to run — you don't need to specify it:

```bash
# → triggers full Planner → Coder → Reviewer pipeline
myapp "add VWAP indicator to the strategy engine"

# → triggers Reviewer only (skips planner + coder)
myapp "review the latest commit before deploying"

# → answered directly by planner, no code written
myapp "should I use asyncio or threading for the data feed?"
```

---

### 💡 Pro Tips

- **Be specific about the file or module** when you know it — it saves the planner from guessing:
  ```bash
  # okay
  myapp "fix the timeout bug"

  # better
  myapp "fix the timeout bug in api/broker.py on the WebSocket reconnect"
  ```

- **Include the error message** for bugs:
  ```bash
  myapp "fix AttributeError: 'NoneType' object has no attribute 'price' in order_manager.py line 84"
  ```

- **Scope refactors clearly** — unbounded refactors often produce too-large plans:
  ```bash
  # risky — very broad scope
  myapp "refactor the whole codebase"

  # better — clear scope
  myapp "refactor the data feed handlers into a single DataFeedManager class"
  ```

- **You control the delegation gate** — after the planner outputs its plan, you'll be asked "Should I delegate this to the coder agent?" Review the plan carefully. Type `n` to get a menu of alternatives: modify the plan, ask a question, switch to review only, or pause.

---

## 📁 Repository Structure

```
auto-agent/
├── README.md
├── LICENSE                          ← MIT
├── opencode/
│   ├── agents/
│   │   ├── planner.md               ← Kimi K2.5
│   │   ├── coder.md                 ← MiniMax M2.5
│   │   ├── reviewer.md              ← GLM-5 (first reviewer)
│   │   └── approver.md              ← MiniMax M2.7 (final approver)
│   ├── opencode.json                ← disables default Build/Plan agents
│   └── orchestrator.py              ← automates the full pipeline
└── examples/
    └── trading-bot/                 ← real world example
        ├── planner.md               ← domain-specific planner
        ├── coder.md                 ← domain-specific coder
        ├── reviewer.md              ← domain-specific reviewer
        └── approver.md              ← domain-specific approver
```

---

## 📄 File Reference

Here's what each file does and what you need to edit before using the pipeline.

---

### `orchestrator.py` — The Pipeline Controller
**Edit required: Yes — one line**

The Python script that runs the entire automated flow. You invoke it via your shell alias and it handles everything from there.

What it does:
- Accepts your task as a quoted CLI argument: `myapp "your task"`
- Runs a **git pre-flight check** before anything else — detects current branch, unpushed commits, and uncommitted changes, then injects this context directly into the planner prompt so it can make informed decisions
- Runs the **Planner** (Kimi K2.5) with the git context already included
- Detects the route tag the planner embeds — `[ROUTE: coder]`, `[ROUTE: reviewer]`, or `[ROUTE: none]`
- Pauses at a **human delegation gate** before any code is written
- If approved, routes to the **Coder** (MiniMax M2.5) with the plan
- Runs **Reviewer** (GLM-5) and **Approver** (MiniMax M2.7) independently — consensus decides the outcome
- If both reject, automatically re-prompts the Coder with the combined issues (up to 3 retries)
- On a split verdict, shows the flagged issues and asks you to decide
- Notifies you to `git pull` to your server on final approval

The only line you need to change:
```python
# Line 20
PROJECT_DIR = "/path/to/your/project"
```

The retry limit is also configurable:
```python
MAX_RETRY_LOOPS = 3
```

---

### `planner.md` — The Planner Agent System Prompt
**Model: `opencode-go/kimi-k2.5`**
**Edit required: Yes — Project Context section**

This is the system prompt that turns Kimi K2.5 into your planner agent. It handles the first step of every pipeline run.

What it does:
- Acts as a **thinker and advisor** — reasons deeply, answers anything, but never executes
- Detects intent across six categories: coding task, review request, committed-but-not-pushed, git commit, general question, or error/debug scenario
- For coding tasks: produces a structured plan then ends with a **delegation gate** — "Should I delegate this to the coder agent?"
- If you say `n`, it offers a menu: modify the plan, ask a question, switch to review only, or pause
- For committed-but-not-pushed: creates a two-step plan — coder pushes first, then reviewer takes over
- For general questions: answers directly with exact bash commands to run manually — no delegation gate, no agent handoff

Update the **Project Context** block to match your stack:
```markdown
## Project Context
- **Language:** Python
- **Framework:** FastAPI/Flask
- **Database:** PostgreSQL/MySQL
- **Cache:** Redis
- **Infrastructure:** Docker
- **Purpose:** Brief description of what your project does
```

Without this, the planner produces generic plans that may not match your codebase structure.

---

### `coder.md` — The Coder Agent System Prompt
**Model: `opencode-go/minimax-m2.5`**
**Edit required: Yes — Project Context + coding rules**

The system prompt for MiniMax M2.5. It receives the approved plan and implements it end-to-end.

What it does:
- Detects intent — refuses planning or review requests and redirects to the correct agent
- Handles a special case: if the planner instructs it to push an unpushed commit, it pushes only — no new code written
- Implements only what the plan specifies — does not touch unrelated code
- Follows strict coding rules: no hardcoded secrets, always handle exceptions, validate inputs, follow existing naming conventions
- Handles the full git workflow: checks version control, shows uncommitted changes, stages, commits with conventional format, and pushes
- Handles unversioned projects: detects missing git repo, asks before running `git init`, optionally connects to a remote URL you provide
- After every push, ends with a **delegation gate** — "Should I delegate this to the reviewer agent?"
- If you say `n`, it offers a menu: make more changes, inspect the commit, skip to approver, go back to planner, or pause

Update the **Project Context** block so the coder knows your stack. You can also add project-specific rules in the commented block:
```markdown
## Project Context
- **Language:** Python
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **Infrastructure:** Docker
- **Purpose:** Brief description of what your project does
```

---

### `reviewer.md` — The Reviewer Agent System Prompt
**Model: `opencode-go/glm-5`**
**Edit required: Yes — Project Context + Critical Issues section**

The first of two independent review agents. Runs after the coder pushes.

What it does:
- Detects intent — refuses to plan or code, only reviews
- Reviews the latest commit for logic errors, security issues, missing error handling, and breaking changes
- Outputs `✅ APPROVED` or `❌ CHANGES NEEDED` with specific issues listed
- If approved, ends with a **delegation gate** — "Should I delegate this to the approver agent?" — if you say `n` it offers alternatives (review again, skip approver, make more changes, or pause)
- If changes needed, ends with a **delegation gate** — "Should I delegate this back to the coder?" — if you say `n` it offers alternatives (fix issues, override and proceed, go back to planner, or pause)

Customise the **Critical Issues** block for your project's domain-specific rules:
```markdown
### 🔴 Critical (must block merge)
- No raw SQL queries — use ORM only
- No changes to payment logic without a feature flag
- All API endpoints must have authentication
```

---

### `approver.md` — The Approver Agent System Prompt
**Model: `opencode-go/minimax-m2.7`**
**Edit required: Yes — Project Context + Critical Issues section**

The final gatekeeper before deployment. Runs after the reviewer, completely independently — it does not see the reviewer's verdict and forms its own opinion.

What it does:
- Detects intent — refuses to plan or code, only approves
- Reviews the same commit independently for the same categories (logic, security, quality, config)
- Outputs `✅ APPROVED` or `❌ CHANGES NEEDED` with its own findings
- If approved, ends with a **deployment gate** — "Are you ready to pull to your server?" — if yes, gives exact `git pull` and Docker rebuild commands; if no, offers alternatives
- If changes needed, ends with a **delegation gate** — "Should I delegate back to the coder?" — if no, offers alternatives (rethink with planner, override and deploy, re-review, or pause)
- The orchestrator compares both verdicts: both approve → deploy, both reject → back to coder, split → you decide

Customise the **Critical Issues** block to match your project — both reviewer and approver should enforce the same rules:

---

### Quick Reference

| File | Model | Edit required | What to change |
|------|-------|---------------|----------------|
| `orchestrator.py` | — | Yes, once | `PROJECT_DIR` on line 20 |
| `planner.md` | Kimi K2.5 | Yes | Project Context block |
| `coder.md` | MiniMax M2.5 | Yes | Project Context + coding rules |
| `reviewer.md` | GLM-5 | Yes | Project Context + Critical Issues block |
| `approver.md` | MiniMax M2.7 | Yes | Project Context + Critical Issues block |

---

## 🔧 Customising for Your Project

Each agent `.md` file has a **Project Context** section — update it for your stack:

```markdown
## Project Context
- **Language:** Python
- **Framework:** FastAPI/Flask
- **Database:** PostgreSQL/MySQL
- **Cache:** Redis
- **Infrastructure:** Docker
- **Purpose:** Your project description here
```

The reviewer also has a **Critical Issues** section — customise what it blocks on:
```markdown
### 🔴 Critical (must block merge)
- Your domain-specific critical checks here
```

---

## 🔄 How the Orchestrator Works

```python
# One command triggers the full pipeline
myapp "add stop loss feature"

# Orchestrator automatically:
# 1. Runs git pre-flight — checks branch, unpushed commits, uncommitted changes
# 2. Injects git context into planner prompt
# 3. Runs planner → captures structured plan
# 4. Pauses for your approval
# 5. Runs coder with the plan → commits + pushes
# 6. Runs reviewer (GLM-5) independently
# 7. Runs approver (MiniMax M2.7) independently
# 8. Evaluates consensus:
#    - Both approved → notify you to deploy
#    - Both rejected → loops back to coder (max 3x)
#    - Split verdict → asks you to decide
```

Each agent runs in a **fresh isolated session** — no context drift, no role confusion.

---

## 🌍 Platform Support

The agent `.md` pattern works across all major AI coding platforms:

| Platform | Config Location | Agent Switching |
|----------|----------------|----------------|
| **OpenCode** | `.opencode/agents/` | `Tab` menu or orchestrator |
| **Claude Code** | `.claude/commands/` | Slash commands |
| **Cursor** | `.cursorrules` | Mode switcher |
| **Aider** | CLI flags | `--system-prompt` |
| **Codex CLI** | `.agents/` | `/agent` command |

Platform-specific implementations coming soon. PRs welcome!

---

## 🤝 Contributing

Contributions are welcome! Ideas:
- Platform-specific orchestrators (Claude Code, Cursor, Aider, Codex)
- Domain-specific agent templates (web app, data pipeline, API service)
- Additional routing logic
- Improved reviewer checklists

Please open an issue first to discuss significant changes.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

Free to use, modify, and distribute. No attribution required (but appreciated!).

---

## 🙏 Acknowledgements

Built with [OpenCode](https://opencode.ai) and [OpenCode Go](https://opencode.ai) models:
- [Kimi K2.5](https://opencode.ai) by Moonshot AI
- [MiniMax M2.5](https://opencode.ai) by MiniMax
- [GLM-5](https://opencode.ai) by Zhipu AI

---

*Built by [PyBankers](https://pybankers.com) — a community for developer-traders.*
