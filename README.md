# 🤖 Multi-Agent Dev Pipeline

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
🧠 Planner  →  💻 Coder  →  🔍 Reviewer
```

The result: **better quality, built-in guardrails, and significantly lower cost.**

---

## 🏗️ Architecture

```
Your task
    ↓
🧠 PLANNER — breaks task into clear steps
    ↓
[Human reviews the plan — approves or rejects]
    ↓
💻 CODER — implements exactly the plan, commits, pushes
    ↓
🔍 REVIEWER — double pass review (bugs + security)
    ↓
✅ APPROVED → pull to your server
❌ CHANGES NEEDED → auto-loops back to coder (max 3 retries)
```

### Smart Routing

The planner intelligently routes tasks to the right agent:

| Route | When | Flow |
|-------|------|------|
| `[ROUTE: coder]` | Feature, fix, or bug | Planner → Coder → Reviewer |
| `[ROUTE: reviewer]` | Check a commit | Reviewer only |
| `[ROUTE: none]` | General question | Planner answers directly |

---

## ✨ Key Features

### 1. Role Boundaries with Intent Detection
Each agent detects when it's being asked to do the wrong job and redirects:
```
User asks coder: "I have a problem, not sure what to do"
Coder responds: "❌ Planning is not my job. Please switch to the planner agent."
```

### 2. Human Approval Gate
After planning, the pipeline pauses for your review before any code is written:
```
⚠️  HUMAN APPROVAL REQUIRED
Review the plan above carefully.
Proceed? (yes/y or no/n):
```

### 3. Double Pass Review
The reviewer runs two independent passes on every commit:
- **Pass 1** — Bug & logic review
- **Pass 2** — Security & quality review

Both passes must agree before approval.

### 4. Auto Retry Loop
If the reviewer rejects, the orchestrator automatically routes back to the coder with the issues — no manual intervention needed. Up to 3 retries before escalating to you.

### 5. Cost Efficient
Uses [OpenCode Go](https://opencode.ai) models — **$5 for your first month, then $10/month** for all three models:

| Agent | Model | Monthly Requests |
|-------|-------|-----------------|
| Planner | Kimi K2.5 | ~9,250 |
| Coder | MiniMax M2.5 | ~100,000 |
| Reviewer | GLM-5 | ~5,750 |

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

### Mode 1 — Automated Pipeline (CLI alias)

```bash
myapp "your task in quotes"
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

> **Rule of thumb:** Know exactly what you want built or fixed? → Use the CLI alias. Want to think it through with an agent first? → Use the TUI.

---

## 🚀 Quick Start

### Prerequisites
- [OpenCode CLI](https://opencode.ai) installed
- [OpenCode Go subscription](https://opencode.ai) ($5 first month, $10/month)
- Python 3.8+

### Installation

**1. Clone the repo**
```bash
git clone https://github.com/sanprat/multi-agent-dev-pipeline.git
cd multi-agent-dev-pipeline
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

**5. Add a shell alias**
```bash
# Add to ~/.zshrc or ~/.bashrc
# Replace "myapp" with whatever name makes sense for your project
alias myapp="python /path/to/your-project/.opencode/orchestrator.py"

source ~/.zshrc
```

> 💡 The alias name is entirely up to you — `myapp`, `devbot`, `trader`, `shopify-bot`, anything. This becomes the command you type to run the pipeline.

**6. Run!**
```bash
myapp "add a user authentication feature"
```

The syntax is always: `your-alias "your task in quotes"`

---

## 🧠 How to Use — Writing Good Prompts

This is a **fire-and-forget pipeline**, not a chat assistant. The prompt you pass in is the only instruction the agents receive — so make it count.

### Syntax

```bash
myapp "your task here"
#  ↑         ↑
#  your      always wrap
#  alias     in quotes
```

Replace `myapp` with whatever alias you set up. The task must always be wrapped in double quotes.

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
myapp "what's the server CPU usage?"              # → check your VPS directly
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

- **You control the approval gate** — after the planner outputs its plan, you'll be asked to approve before any code is written. Read it carefully and type `n` to abort if it doesn't look right.

---

## 📁 Repository Structure

```
multi-agent-dev-pipeline/
├── README.md
├── LICENSE                          ← MIT
├── opencode/
│   ├── agents/
│   │   ├── planner.md               ← Kimi K2.5
│   │   ├── coder.md                 ← MiniMax M2.5
│   │   └── reviewer.md              ← GLM-5 (double pass)
│   ├── opencode.json                ← disables default Build/Plan agents
│   └── orchestrator.py              ← automates the full pipeline
└── examples/
    └── trading-bot/                 ← real world example
        ├── planner.md               ← domain-specific planner
        ├── coder.md                 ← domain-specific coder
        └── reviewer.md              ← domain-specific reviewer
```

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
# 1. Runs planner → captures structured plan
# 2. Pauses for your approval
# 3. Runs coder with the plan → commits + pushes
# 4. Runs reviewer (double pass) → reads verdict
# 5. If APPROVED → notifies you to deploy
# 6. If CHANGES NEEDED → loops back to coder (max 3x)
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
