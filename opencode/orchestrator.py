#!/usr/bin/env python3
"""
auto-agent — Multi-Agent Dev Pipeline Orchestrator
====================================================
Planner (Kimi K2.5) → [Human Approval] → Smart Route
    → [ROUTE: none]     → Planner answers directly, no agents needed
    → [ROUTE: reviewer] → Reviewer (GLM-5) + Approver (MiniMax M2.7) → Consensus
    → [ROUTE: coder]    → Coder (MiniMax M2.5) → Reviewer + Approver → Consensus

Pre-flight: Git status is automatically checked and injected into planner context.

Consensus rules:
    Both APPROVED       → ✅ Deploy
    Both CHANGES NEEDED → ❌ Auto-route to coder
    Split verdict       → ⚠️  Ask human to decide

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
MAX_RETRY_LOOPS = 3                     # max times coder retries after rejection

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

def get_git_context() -> str:
    """
    Check git status before running planner.
    Returns a git context string injected into the planner prompt.
    """
    try:
        # Check for unpushed commits
        unpushed = subprocess.run(
            ["git", "log", "origin/main..HEAD", "--oneline"],
            capture_output=True, text=True, cwd=PROJECT_DIR
        )

        # Check for uncommitted changes
        status = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True, text=True, cwd=PROJECT_DIR
        )

        # Check current branch
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=PROJECT_DIR
        )

        unpushed_commits = unpushed.stdout.strip()
        uncommitted_changes = status.stdout.strip()
        current_branch = branch.stdout.strip()

        context_lines = ["\n--- GIT CONTEXT (auto-detected) ---"]
        context_lines.append(f"Branch: {current_branch}")

        if unpushed_commits:
            context_lines.append(f"⚠️  Unpushed commits detected:\n{unpushed_commits}")
        else:
            context_lines.append("✅ All commits are pushed to remote.")

        if uncommitted_changes:
            context_lines.append(f"⚠️  Uncommitted changes detected:\n{uncommitted_changes}")
        else:
            context_lines.append("✅ Working tree is clean — no uncommitted changes.")

        context_lines.append("--- END GIT CONTEXT ---\n")

        git_context = "\n".join(context_lines)
        print(f"\n  🔍 Git pre-flight check:")
        print(f"     Branch: {current_branch}")
        print(f"     Unpushed commits: {'Yes' if unpushed_commits else 'None'}")
        print(f"     Uncommitted changes: {'Yes' if uncommitted_changes else 'None'}")

        return git_context

    except Exception as e:
        print(f"  ⚠️  Git pre-flight check failed: {e}")
        return "\n--- GIT CONTEXT ---\nUnable to check git status automatically.\n--- END GIT CONTEXT ---\n"

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
    """Check if agent approved the commit."""
    return "APPROVED" in review_output.upper()

def notify(message: str):
    """Print a prominent notification to the user."""
    width = 60
    print("\n" + "★" * width)
    print(f"  {message}")
    print("★" * width + "\n")
    sys.stdout.flush()

def run_review_and_approval(attempt: int = 1) -> tuple:
    """
    Run reviewer (GLM-5) then approver (MiniMax M2.7) independently.
    Returns (both_approved, both_rejected, is_split, combined, review, approval)
    """
    # REVIEWER — GLM-5
    print_banner("reviewer", "GLM-5", f"→ REVIEWER (attempt {attempt})")
    review = run_agent(
        agent="reviewer",
        prompt="Review the latest git commit independently. Output APPROVED or CHANGES NEEDED with full details."
    )
    if not review:
        print("❌ Reviewer returned no output. Aborting.")
        sys.exit(1)

    # APPROVER — MiniMax M2.7
    print_banner("approver", "MiniMax M2.7", f"→ APPROVER (attempt {attempt})")
    approval = run_agent(
        agent="approver",
        prompt="Review the latest git commit independently for final approval. Output APPROVED or CHANGES NEEDED with full details."
    )
    if not approval:
        print("❌ Approver returned no output. Aborting.")
        sys.exit(1)

    r_approved = is_approved(review)
    a_approved = is_approved(approval)
    both_approved = r_approved and a_approved
    both_rejected = not r_approved and not a_approved
    is_split = r_approved != a_approved

    # Print consensus summary
    print_divider()
    print(f"  📊 REVIEW & APPROVAL CONSENSUS:")
    print(f"     Reviewer (GLM-5):        {'✅ APPROVED' if r_approved else '❌ CHANGES NEEDED'}")
    print(f"     Approver (MiniMax M2.7): {'✅ APPROVED' if a_approved else '❌ CHANGES NEEDED'}")

    if both_approved:
        print(f"     Result: ✅ CONSENSUS — Both approved")
    elif both_rejected:
        print(f"     Result: ❌ CONSENSUS — Both rejected")
    else:
        print(f"     Result: ⚠️  SPLIT VERDICT — Human decision required")
    print_divider()

    combined = f"REVIEWER (GLM-5):\n{review}\n\nAPPROVER (MiniMax M2.7):\n{approval}"
    return both_approved, both_rejected, is_split, combined, review, approval

def handle_split_verdict(review: str, approval: str, r_approved: bool) -> bool:
    """
    Handle split verdict — show flagged issues and ask human to decide.
    Returns True if human decides to send to coder, False to approve and deploy.
    """
    print("\n  ⚠️  SPLIT VERDICT DETECTED")
    print("  One agent approved, one requested changes.\n")

    if not r_approved:
        print("  ❌ Reviewer (GLM-5) flagged these issues:")
        print("  " + "─" * 56)
        lines = [l for l in review.split('\n') if l.strip()]
        for line in lines[-10:]:
            print(f"     {line}")
    else:
        print("  ❌ Approver (MiniMax M2.7) flagged these issues:")
        print("  " + "─" * 56)
        lines = [l for l in approval.split('\n') if l.strip()]
        for line in lines[-10:]:
            print(f"     {line}")

    print_divider()
    print("  You decide:")
    print("  → yes/y = Send to coder to fix the flagged issues")
    print("  → no/n  = Ignore the flag and approve for deploy")
    print()

    return ask_human("Send to coder to fix?")

def review_and_fix_loop(initial_coder_prompt: str = None) -> bool:
    """
    Shared loop for both coder and reviewer-only routes.
    If initial_coder_prompt is None, skips first coder run (reviewer-only route).
    Returns True if finally approved, False if max retries reached.
    """
    attempt = 0
    code_approved = False
    combined = ""
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

        # Reviewer + Approver consensus
        both_approved, both_rejected, is_split, combined, review, approval = run_review_and_approval(attempt)
        r_approved = is_approved(review)

        if both_approved:
            code_approved = True

        elif both_rejected:
            if attempt < MAX_RETRY_LOOPS:
                print(f"\n  🔄 Both rejected. Routing to coder... (attempt {attempt}/{MAX_RETRY_LOOPS})")
                coder_prompt = f"Both reviewer and approver rejected the commit. Fix these issues:\n\n{combined}"
                skip_coder_first = False
            else:
                print(f"\n  ❌ Max retries ({MAX_RETRY_LOOPS}) reached. Manual intervention needed.")

        elif is_split:
            send_to_coder = handle_split_verdict(review, approval, r_approved)
            if send_to_coder:
                if attempt < MAX_RETRY_LOOPS:
                    flagged = review if not r_approved else approval
                    coder_prompt = f"One agent flagged these issues. Fix them:\n\n{flagged}"
                    skip_coder_first = False
                else:
                    print(f"\n  ❌ Max retries ({MAX_RETRY_LOOPS}) reached. Manual intervention needed.")
            else:
                print("\n  ✅ Human overriding split verdict — approving for deploy.")
                code_approved = True

    return code_approved

# ─────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python orchestrator.py \"your task here\"")
        sys.exit(1)

    task = " ".join(sys.argv[1:])

    print(f"\n🚀 auto-agent Pipeline Starting")
    print(f"   Task: {task}")
    print(f"   Time: {timestamp()}")
    sys.stdout.flush()

    # ─────────────────────────────────────
    # PRE-FLIGHT: GIT STATUS CHECK
    # ─────────────────────────────────────
    print_divider()
    print("  🔍 Running git pre-flight check...")
    git_context = get_git_context()
    print_divider()

    # ─────────────────────────────────────
    # STEP 1: PLANNER (with git context injected)
    # ─────────────────────────────────────
    print_banner("planner", "Kimi K2.5", "1 → PLANNER")
    planner_prompt = f"{git_context}User task: {task}"
    plan = run_agent(
        agent="planner",
        prompt=planner_prompt
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
    # ROUTE: REVIEWER + APPROVER ONLY
    # ─────────────────────────────────────
    if route == "reviewer":
        final_approved = review_and_fix_loop(initial_coder_prompt=None)

    # ─────────────────────────────────────
    # ROUTE: CODER → REVIEWER + APPROVER
    # ─────────────────────────────────────
    else:
        final_approved = review_and_fix_loop(
            initial_coder_prompt=f"Here is the plan to implement:\n\n{plan}"
        )

    # ─────────────────────────────────────
    # FINAL OUTCOME
    # ─────────────────────────────────────
    if final_approved:
        notify("✅ REVIEWER & APPROVER CONSENSUS — Pull to your server when ready:\n   git pull origin main")
    else:
        notify("❌ CHANGES NEEDED — Review the issues above and re-run.")
        sys.exit(1)

if __name__ == "__main__":
    main()
