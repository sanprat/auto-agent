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

## ⚠️ Important: When to Use This Framework

This orchestrator is designed for **software engineering tasks only**:

✅ **Use `pytrader "task"` for:**
- Building new features
- Fixing bugs
- Reviewing commits before deployment
- Refactoring code

❌ **Do NOT use for:**
- Interactive Q&A or conversational help
- VPS/system status checks
- Real-time data queries
- Anything requiring mid-flow human interaction

> For interactive tasks, open OpenCode TUI directly and use the planner agent conversationally.

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
alias myproject="python /path/to/your/project/.opencode/orchestrator.py"
source ~/.zshrc
```

**6. Run!**
```bash
myproject "add a user authentication feature"
```

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
myproject "add stop loss feature"

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
