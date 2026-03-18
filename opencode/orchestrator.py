#!/usr/bin/env python3
"""
Multi-Agent Dev Pipeline — Orchestrator
========================================
Planner → [Human Approval] → Smart Route
    → [ROUTE: none]     → Planner answers directly, no agents needed
    → [ROUTE: reviewer] → Reviewer (double pass) → Human notified
    → [ROUTE: coder]    → Coder → Reviewer (double pass)

Reviewer runs two independent passes internally.
If APPROVED → notify human to pull to server.
If CHANGES NEEDED → auto-route to coder, retry up to 3 times.

Usage:
    python orchestrator.py "your task here"
"""

import subprocess
import sys
from datetime import datetime

# ─────────────────────────────────────────
# CONFIG — update these before first run
# ─────────────────────────────────────────
PROJECT_DIR = "/path/to/your/project"   # ← change this to your project path
MAX_RETRY_LOOPS = 3                     # max times coder retries after reviewer rejects

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────

def print_banner(agent: str, model: str, step: str):
    width = 60
    print("\n" + "═" * width)
    print(f"  STEP {step}  →  [{agent.upper()}] agent  ({model})")
    print("═" * width + "\n")
    sys.stdout.flush()

def print_divider():
    print("\n" + "─" * 60 + "\n")
    sys.stdout.flush()

def timestamp():
    return datetime.now().strftime("%H:%M:%S")

def run_agent(agent: str, prompt: str) -> str:
    """Run an OpenCode agent, stream output in real time, and return full output."""
    cmd = ["opencode", "run", "--agent", agent, prompt]

    print(f"  [{timestamp()}] Running {agent}...\n")
    sys.stdout.flush()

    output_lines = []

    with subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=PROJECT_DIR,
        bufsize=1
    ) as proc:
        for line in proc.stdout:
            print(line, end="")
            sys.stdout.flush()
            output_lines.append(line)

    full_output = "".join(output_lines).strip()
    return full_output

def detect_route(plan_output: str) -> str:
    """Detect routing tag from planner output."""
    if "[ROUTE: none]" in plan_output:
        return "none"
    elif "[ROUTE: reviewer]" in plan_output:
        return "reviewer"
    elif "[ROUTE: coder]" in plan_output:
        return "coder"
    else:
        print("  ⚠️  No route tag detected. Defaulting to full pipeline (coder → reviewer).")
        return "coder"

def ask_human(question: str) -> bool:
    """Ask user a yes/no question and return their decision."""
    while True:
        try:
            response = input(f"  {question} (yes/y or no/n): ").strip().lower()
            if response in ["yes", "y"]:
                return True
            elif response in ["no", "n"]:
                return False
            else:
                print("  Please type 'yes/y' or 'no/n'")
        except KeyboardInterrupt:
            print("\n\n  ⛔ Pipeline interrupted by user.")
            sys.exit(0)

def is_approved(review_output: str) -> bool:
    """Check if reviewer approved the commit."""
    return "APPROVED" in review_output.upper()

def notify(message: str):
    """Print a prominent notification to the user."""
    width = 60
    print("\n" + "★" * width)
    print(f"  {message}")
    print("★" * width + "\n")
    sys.stdout.flush()

def run_reviewer(attempt: int = 1) -> str:
    """Run the double pass reviewer and return full output."""
    print_banner("reviewer", "GLM-5 (double pass)", f"→ REVIEWER (attempt {attempt})")
    review = run_agent(
        agent="reviewer",
        prompt="Review the latest git commit using your double pass process. Pass 1: bugs and logic. Pass 2: security and quality. Output APPROVED or CHANGES NEEDED with full details."
    )
    if not review:
        print("❌ Reviewer returned no output. Aborting.")
        sys.exit(1)
    return review

def review_and_fix_loop(initial_coder_prompt: str = None) -> bool:
    """
    Shared loop for both coder and reviewer-only routes.
    If initial_coder_prompt is None, skips first coder run (reviewer-only route).
    Returns True if finally approved, False if max retries reached.
    """
    attempt = 0
    code_approved = False
    review = ""
    skip_coder_first = initial_coder_prompt is None
    coder_prompt = initial_coder_prompt

    while attempt < MAX_RETRY_LOOPS and not code_approved:
        attempt += 1

        # Run coder unless this is reviewer-only first pass
        if not (skip_coder_first and attempt == 1):
            print_banner("coder", "MiniMax M2.5", f"→ CODER (attempt {attempt}/{MAX_RETRY_LOOPS})")
            code_result = run_agent(agent="coder", prompt=coder_prompt)
            if not code_result:
                print("❌ Coder returned no output. Aborting.")
                sys.exit(1)

        # Double pass review
        review = run_reviewer(attempt)

        if is_approved(review):
            code_approved = True
        else:
            if attempt < MAX_RETRY_LOOPS:
                print(f"\n  🔄 Reviewer rejected. Routing to coder... (attempt {attempt}/{MAX_RETRY_LOOPS})")
                coder_prompt = f"The reviewer rejected the commit after double pass review. Fix these issues:\n\n{review}"
                skip_coder_first = False
            else:
                print(f"\n  ❌ Max retries ({MAX_RETRY_LOOPS}) reached. Manual intervention needed.")

    return code_approved

# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py \"your task here\"")
        sys.exit(1)

    task = " ".join(sys.argv[1:])

    print(f"\n🚀 Multi-Agent Pipeline Starting")
    print(f"   Task: {task}")
    print(f"   Time: {timestamp()}")
    sys.stdout.flush()

    # ─────────────────────────────────────
    # STEP 1: PLANNER
    # ─────────────────────────────────────
    print_banner("planner", "Kimi K2.5", "1 → PLANNER")
    plan = run_agent(
        agent="planner",
        prompt=task
    )

    if not plan:
        print("❌ Planner returned no output. Aborting.")
        sys.exit(1)

    # ─────────────────────────────────────
    # STEP 2: DETECT ROUTE
    # ─────────────────────────────────────
    route = detect_route(plan)
    print(f"\n  🔀 Route detected: [{route.upper()}]")
    sys.stdout.flush()

    # ─────────────────────────────────────
    # ROUTE: NONE — Planner answered directly
    # ─────────────────────────────────────
    if route == "none":
        print("\n  💡 Planner answered directly. No agents needed.")
        sys.exit(0)

    # ─────────────────────────────────────
    # STEP 3: HUMAN APPROVAL GATE
    # (only for coder and reviewer routes)
    # ─────────────────────────────────────
    print_divider()
    print("  ⚠️  HUMAN APPROVAL REQUIRED")
    print("  Review the plan above carefully.")
    print_divider()

    if not ask_human("Proceed?"):
        print("\n  ⛔ Pipeline stopped by user.")
        print("  💡 Tip: Refine your task and re-run:")
        print(f"     myapp \"your updated task here\"")
        print()
        sys.exit(0)

    print(f"\n  ✅ Approved! Routing to [{route.upper()}]...\n")
    sys.stdout.flush()

    # ─────────────────────────────────────
    # ROUTE: REVIEWER ONLY
    # ─────────────────────────────────────
    if route == "reviewer":
        final_approved = review_and_fix_loop(initial_coder_prompt=None)

    # ─────────────────────────────────────
    # ROUTE: CODER → REVIEWER
    # ─────────────────────────────────────
    else:
        final_approved = review_and_fix_loop(
            initial_coder_prompt=f"Here is the plan to implement:\n\n{plan}"
        )

    # ─────────────────────────────────────
    # FINAL OUTCOME
    # ─────────────────────────────────────
    if final_approved:
        notify("✅ REVIEWER APPROVED (double pass) — Pull to your server when ready:\n   git pull origin main")
    else:
        notify("❌ CHANGES NEEDED — Review the issues above and re-run.")
        sys.exit(1)

if __name__ == "__main__":
    main()
