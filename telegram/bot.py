import json
import time
import threading
from typing import Dict, Any, List
import requests
from configs.config import config
from database.db import db
from memory.memory_manager import memory_manager
from orchestrator.orchestrator import orchestrator
from orchestrator.resolver import project_resolver
from planner.planner import task_planner

class TelegramBot:
    def __init__(self):
        self.token = config.telegram_bot_token
        self.chat_id = config.telegram_chat_id
        self.base_url = f"https://api.telegram.org/bot{self.token}" if self.token else None
        self.offset = 0
        self.running = False
        
        # State machine for human approval
        # maps chat_id -> task pending details
        self.approval_state: Dict[str, Dict[str, Any]] = {}

    def send_message(self, chat_id: str, text: str) -> bool:
        if not self.base_url or not chat_id:
            print(f"[Telegram MOCK Send to {chat_id}]: {text}")
            return True
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code != 200:
                print(f"Telegram API Error (Status {res.status_code}): {res.text}")
            return res.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False

    def send_chat_action(self, chat_id: str, action: str = "typing") -> bool:
        if not self.base_url or not chat_id:
            return True
        url = f"{self.base_url}/sendChatAction"
        payload = {
            "chat_id": chat_id,
            "action": action
        }
        try:
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram chat action: {e}")
            return False

    def start(self):
        if not self.token:
            db.log("telegram", "WARNING", "No Telegram bot token found in config. Running in MOCK terminal-input mode.")
            self._start_terminal_loop()
            return

        self.running = True
        t = threading.Thread(target=self._poll_loop, daemon=True)
        t.start()
        db.log("telegram", "INFO", "Telegram bot polling loop started.")

    def stop(self):
        self.running = False

    def _poll_loop(self):
        db.log("telegram", "INFO", "Entering Telegram getUpdates loop...")
        while self.running:
            url = f"{self.base_url}/getUpdates"
            params = {"offset": self.offset, "timeout": 20}
            try:
                res = requests.get(url, params=params, timeout=25)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("ok"):
                        for update in data.get("result", []):
                            self.offset = update["update_id"] + 1
                            self._handle_update(update)
                else:
                    time.sleep(5)
            except Exception as e:
                time.sleep(5)

    def _start_terminal_loop(self):
        """Allows debugging locally when Telegram is not configured."""
        def t_loop():
            print("\n=== AI OS Mock Terminal Interface ===")
            print("Type messages to simulate Telegram commands. Type 'exit' to quit.")
            while True:
                try:
                    user_input = input("AI OS > ").strip()
                    if user_input.lower() == 'exit':
                        break
                    
                    # Construct mock update
                    mock_update = {
                        "message": {
                            "chat": {"id": "terminal_user"},
                            "text": user_input,
                            "message_id": int(time.time())
                        }
                    }
                    self._handle_update(mock_update)
                except (KeyboardInterrupt, EOFError):
                    break
        
        threading.Thread(target=t_loop, daemon=True).start()

    def _handle_update(self, update: Dict[str, Any]):
        msg = update.get("message")
        if not msg:
            return

        chat = msg.get("chat", {})
        chat_id = str(chat.get("id"))
        text = msg.get("text", "").strip()
        msg_id = msg.get("message_id")

        if not text:
            return

        # 1. Check if we are waiting for human approval response from this chat
        if chat_id in self.approval_state:
            self._handle_approval_response(chat_id, text)
            return

        # 2. Route Commands
        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""
            
            if cmd in ["/start", "/help"]:
                self._cmd_start(chat_id)
            elif cmd == "/task":
                self._cmd_task(chat_id, arg)
            elif cmd == "/status":
                self._cmd_status(chat_id)
            elif cmd == "/projects":
                self._cmd_projects(chat_id)
            elif cmd == "/logs":
                self._cmd_logs(chat_id)
            elif cmd == "/skills":
                self._cmd_skills(chat_id)
            else:
                self.send_message(chat_id, f"Unknown command: {cmd}\nTry /start, /task, /status, /projects, /logs, /skills")
        else:
            # Natural Language orchestrator processing in background thread
            threading.Thread(
                target=self._process_natural_language,
                args=(chat_id, text),
                daemon=True
            ).start()

    # --- COMMAND HANDLERS ---

    def _cmd_start(self, chat_id: str):
        welcome = (
            "🤖 *Welcome to Personal AI OS (aios)!*\n\n"
            "You can talk to me directly in natural language (without `/`). "
            "Just type what you want me to do (e.g. 'Run pytest on Sahas' or 'Check pybankers git status'), "
            "and my OpenRouter Orchestrator will plan, execute, and verify it!\n\n"
            "*Available commands:*\n"
            "- `/task <desc>`: Queue a task\n"
            "- `/status`: Get status of recent runs\n"
            "- `/projects`: List your resolved project paths\n"
            "- `/skills`: List custom registered developer skills\n"
            "- `/logs`: View recent system logs\n"
            "- `/help`: Show this help message"
        )
        self.send_message(chat_id, welcome)

    def _cmd_task(self, chat_id: str, arg: str):
        if not arg:
            self.send_message(chat_id, "Usage: `/task <description of task>`")
            return
        self._process_natural_language(chat_id, arg)

    def _cmd_status(self, chat_id: str):
        recent = db.get_recent_tasks(5)
        if not recent:
            self.send_message(chat_id, "No tasks executed yet.")
            return

        resp = "*Recent Task Statuses:*\n"
        for t in recent:
            status_emoji = "⏳"
            if t['status'] == 'completed':
                status_emoji = "✅"
            elif t['status'] == 'failed':
                status_emoji = "❌"
            elif t['status'] == 'running':
                status_emoji = "⚙️"
                
            v_emoji = "🛡️" if t['verification_status'] == 'verified' else "⚠️" if t['verification_status'] == 'failed' else "❔"
            
            resp += f"{status_emoji} `{t['id'][:8]}` - {t['description'][:30]}... ({t['status']})\n"
            resp += f"   Verification: {t['verification_status']} {v_emoji}\n"
        self.send_message(chat_id, resp)

    def _cmd_projects(self, chat_id: str):
        projects = project_resolver.get_all_projects()
        if not projects:
            self.send_message(chat_id, "No configured projects found in Project Resolver.")
            return

        resp = "*Configured Projects:*\n"
        for name, path in projects.items():
            resp += f"- *{name}*: `{path}`\n"
        self.send_message(chat_id, resp)

    def _cmd_logs(self, chat_id: str):
        logs = db.get_logs(limit=10)
        if not logs:
            self.send_message(chat_id, "No logs recorded yet.")
            return

        resp = "*Recent System Logs:*\n"
        for l in reversed(logs):
            resp += f"`[{l['timestamp'].split()[-1]}]` `[{l['log_level']}]` {l['message'][:60]}\n"
        self.send_message(chat_id, resp)

    def _cmd_skills(self, chat_id: str):
        skills = db.get_all_skills()
        if not skills:
            self.send_message(chat_id, "No custom skills registered in your skill library.")
            return

        resp = "*Skill Library:*\n"
        for s in skills:
            resp += f"- *{s['name']}*: {s['description'] or 'No description'}\n"
        self.send_message(chat_id, resp)

    # --- PROCESS NATURAL LANGUAGE & PLANS ---

    def _process_natural_language(self, chat_id: str, prompt: str):
        self.send_chat_action(chat_id, "typing")
        
        try:
            # 1. Call OpenRouter to plan
            plan = orchestrator.plan_request(prompt)
            
            # Check if this is a conversational request
            if plan.get("is_conversational", False):
                response_text = plan.get("response", "I understand your request.")
                self.send_message(chat_id, response_text)
                return

            reasoning = plan.get("reasoning", plan.get("response", "No details"))
            self.send_message(chat_id, f"📝 *Reasoning:*\n{reasoning}")

            tasks = plan.get("tasks", [])
            if not tasks:
                self.send_message(chat_id, "❌ Orchestrator was unable to generate actionable subtasks.")
                return

            # 2. Check for human approval actions
            sensitive_keywords = ["push", "deploy", "delete", "rm ", "drop", "migrate"]
            needs_approval = False
            sensitive_desc = ""
            
            for t in tasks:
                cmd_lower = t.get("command", "").lower()
                desc_lower = t.get("description", "").lower()
                if any(kw in cmd_lower or kw in desc_lower for kw in sensitive_keywords):
                    needs_approval = True
                    sensitive_desc = t.get("description")
                    break

            if needs_approval:
                self.send_message(
                    chat_id, 
                    f"⚠️ *Human Approval Required:*\n"
                    f"Plan contains sensitive operations: *{sensitive_desc}*\n\n"
                    f"Do you approve this plan? Reply *YES* to execute, or *NO* to cancel."
                )
                self.approval_state[chat_id] = {
                    "plan": plan,
                    "prompt": prompt
                }
            else:
                # Direct execution
                self._execute_orchestrated_plan(chat_id, plan)

        except Exception as e:
            self.send_message(chat_id, f"❌ Orchestration error: {e}")

    def _handle_approval_response(self, chat_id: str, response_text: str):
        state = self.approval_state.pop(chat_id)
        if response_text.strip().upper() in ["YES", "Y", "APPROVE"]:
            self.send_message(chat_id, "✅ Plan approved. Starting execution...")
            threading.Thread(
                target=self._execute_orchestrated_plan,
                args=(chat_id, state["plan"]),
                daemon=True
            ).start()
        else:
            self.send_message(chat_id, "❌ Execution cancelled by human operator.")

    def _execute_orchestrated_plan(self, chat_id: str, plan: Dict[str, Any]):
        self.send_message(chat_id, f"⚙️ Running {len(plan.get('tasks', []))} tasks...")
        
        try:
            # Run sequential planner
            executed = task_planner.execute_plan(plan)
            
            # Formulate final report
            report = "*Execution Summary:*\n"
            success_count = 0
            for t in executed:
                status_emoji = "✅" if t["status"] == "completed" else "❌"
                v_emoji = "🛡️" if t['verification_status'] == 'verified' else "⚠️" if t['verification_status'] == 'failed' else "❔"
                report += f"{status_emoji} `{t['id'][:8]}` - {t['description']} ({t['status']} {v_emoji})\n"
                
                if t.get("output"):
                    out = t["output"].strip()
                    if out:
                        if len(out) <= 300:
                            report += f"```\n{out}\n```\n"
                        else:
                            # Highlight any lines containing URL/tunnel info
                            lines = out.splitlines()
                            url_lines = [line for line in lines if any(k in line.lower() for k in ["url", "http", "tunnel", "loca.lt"])]
                            if url_lines:
                                report += f"```\n" + "\n".join(url_lines) + "\n```\n"
                            else:
                                fallback_out = lines[:3] + ["..."] + lines[-3:] if len(lines) > 6 else lines
                                report += f"```\n" + "\n".join(fallback_out) + "\n```\n"
                
                if t["status"] == "completed":
                    success_count += 1
                    
            # Save task execution outputs back to conversation history so OpenRouter remembers them!
            exec_context = "Task execution outputs:\n"
            for t in executed:
                output_str = t.get("output") or ""
                # Strip excessive output for token space
                if len(output_str) > 1000:
                    output_str = output_str[:1000] + "\n...[truncated]..."
                exec_context += f"- Task: '{t['description']}' | Status: {t['status']} | Output:\n{output_str}\n"
            
            memory_manager.add_conversation("user", f"[System Event / Task Output]:\n{exec_context[:4000]}")

            if success_count == len(executed):
                report += "\n🎉 *All tasks executed and verified successfully!*"
            else:
                report += "\n⚠️ *Some tasks failed or verification check failed. Check logs.*"
                
            self.send_message(chat_id, report)
            
        except Exception as e:
            self.send_message(chat_id, f"❌ Execution manager error: {e}")

# Global bot instance
bot = TelegramBot()
