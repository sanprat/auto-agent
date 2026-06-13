import json
import requests
import re
import uuid
from typing import Dict, List, Any, Tuple
from configs.config import config
from orchestrator.resolver import project_resolver
from memory.memory_manager import memory_manager
from database.db import db

class OpenRouterOrchestrator:
    def __init__(self):
        self.api_key = config.openrouter_api_key
        self.model = config.openrouter_model
        self.base_url = config.openrouter_base_url
        self.reasoning_enabled = config.reasoning_enabled

    def _call_openrouter(self, messages: List[Dict[str, Any]]) -> Tuple[str, Any]:
        """
        Sends chat history to OpenRouter API and extracts content and reasoning_details.
        """
        if not self.api_key:
            return self._fallback_local_response(messages)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
        }
        
        # Only enable reasoning parameters if configured
        if self.reasoning_enabled:
            payload["reasoning"] = {"enabled": True}

        try:
            db.log("orchestrator", "INFO", f"Calling OpenRouter model: {self.model}")
            response = requests.post(
                url=f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=180
            )
            response.raise_for_status()
            resp_data = response.json()
            
            choice = resp_data['choices'][0]['message']
            content = choice.get('content', '')
            reasoning_details = choice.get('reasoning_details', None)
            
            return content, reasoning_details

        except Exception as e:
            db.log("orchestrator", "ERROR", f"OpenRouter API call failed: {e}")
            return self._fallback_local_response(messages)

    def _fallback_local_response(self, messages: List[Dict[str, Any]]) -> Tuple[str, Any]:
        """
        Local heuristic fallback if OpenRouter is unconfigured/offline.
        """
        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"]
                break
        
        db.log("orchestrator", "WARNING", f"Using offline fallback orchestrator parsing.")
        
        # Simple regex matcher for fallback
        project_name = None
        for p in ["pybankers", "sahas", "games", "experiments"]:
            if p in last_user_msg.lower():
                project_name = p
                break
        
        if "test" in last_user_msg.lower():
            fallback_json = {
                "is_conversational": False,
                "project_name": project_name or "experiments",
                "reasoning": "User wants to test. Running tests.",
                "tasks": [
                    {
                        "id": f"task_{uuid.uuid4().hex[:8]}",
                        "description": "Run project tests",
                        "worker_type": "cmd",
                        "command": "pytest" if "python" in last_user_msg.lower() else "npm test"
                    }
                ]
            }
        else:
            fallback_json = {
                "is_conversational": False,
                "project_name": project_name or "experiments",
                "reasoning": "Offline parsing of command.",
                "tasks": [
                    {
                        "id": f"task_{uuid.uuid4().hex[:8]}",
                        "description": f"Execute request: {last_user_msg}",
                        "worker_type": "cmd",
                        "command": "echo 'AI OS executed command in offline fallback'"
                    }
                ]
            }
            
        return json.dumps(fallback_json, indent=2), "Local Offline Reasoning"

    def plan_request(self, user_prompt: str) -> Dict[str, Any]:
        """
        Takes user input, injects relevant memory and skills, calls LLM,
        and parses the returned task plan.
        """
        # 1. Resolve project if mentioned
        project_name = None
        for p in project_resolver.get_all_projects().keys():
            if p.lower() in user_prompt.lower():
                project_name = p
                break
        
        # 2. Get memory context
        memory_context = memory_manager.get_relevant_context(user_prompt, project_name)

        # 3. Get skills context
        skills = db.get_all_skills()
        skills_context = "Available custom skills:\n"
        if skills:
            for s in skills:
                skills_context += f"- {s['name']}: {s['description']}\n"
        else:
            skills_context += "- None registered.\n"

        system_prompt = f"""You are the main orchestrator (Manager Agent) of a Personal AI OS.
Your job is to understand the user's request, look at the contextual memory, and output a structured task plan or a natural chat response.

{memory_context}

{skills_context}

Output your response STRICTLY as a JSON object of this structure:
{{
  "is_conversational": true or false,
  "response": "your direct conversational reply to the user (use this for general talk, questions, greetings, or explanations)",
  "project_name": "resolved project name or null",
  "reasoning": "your detailed planning process (only if is_conversational is false)",
  "tasks": [
    {{
      "id": "unique_id_1",
      "description": "Short explanation of this subtask",
      "worker_type": "cmd | browser",
      "command": "the shell command, python execution script, or URL to fetch"
    }}
  ]
}}

Guidelines:
- If the user is just chatting, asking a general question (e.g. "what can you build?", "hello", "how are you"), or requesting explanation, set "is_conversational" to true, write your answer in "response", and set "tasks" to [].
- Only if the user explicitly commands you to build, modify, delete, test, or execute code/commands, set "is_conversational" to false, outline your plan in "reasoning", and specify the worker tasks list.
- Choose 'cmd' for running shell commands, starting background/local servers, executing python scripts, and running CLI tools.
- To perform code generation or file modifications, use the 'cmd' worker type with the multi-agent orchestrator command: `python experiments/auto-agent/opencode/orchestrator.py -y "<your coding prompt>"` (e.g. `{{"id": "create_game", "description": "Create snake game", "worker_type": "cmd", "command": "python experiments/auto-agent/opencode/orchestrator.py -y 'Create snake game in index.html'"}}`).
- Choose 'browser' for crawling, scraping, or fetching web pages/URLs.
- If a coding/file creation task (using the 'cmd' multi-agent orchestrator command) is planned, explicitly mention in your reasoning/response that:
  "I will plan the task, send to coder, and coder after creating the task sends it to the approver (Kimi K2.7 Code) for final approval."
- ALWAYS return ONLY raw JSON without markdown codeblock wrapper tags, or if you use them, format properly.
"""

        # 4. Construct messages history (retrieve recent conversations)
        history = memory_manager.get_conversation_history(10)
        messages = [{"role": "system", "content": system_prompt}]
        
        for msg in history:
            msg_dict = {"role": msg["role"], "content": msg["content"]}
            if msg.get("reasoning_details"):
                try:
                    msg_dict["reasoning_details"] = json.loads(msg["reasoning_details"])
                except Exception:
                    msg_dict["reasoning_details"] = msg["reasoning_details"]
            messages.append(msg_dict)
            
        messages.append({"role": "user", "content": user_prompt})

        # 5. Call OpenRouter
        content, reasoning_details = self._call_openrouter(messages)

        # Save conversations in short-term database
        memory_manager.add_conversation("user", user_prompt)
        memory_manager.add_conversation("assistant", content, reasoning_details=reasoning_details)

        # 6. Parse JSON output
        parsed_plan = self._clean_and_parse_json(content)
        if not parsed_plan:
            # Re-run or return fallback
            parsed_plan = self._clean_and_parse_json(self._fallback_local_response(messages)[0])

        # Enforce opencode-go multi-agent routing for code modification/creation
        if not parsed_plan.get("is_conversational", False):
            new_tasks = []
            for t in parsed_plan.get("tasks", []):
                w_type = t.get("worker_type", "")
                is_coding = False
                coding_prompt = user_prompt  # Default fallback
                
                if w_type == "freebuff":
                    is_coding = True
                    cmd_str = t.get("command", "")
                    try:
                        import json
                        cmd_json = json.loads(cmd_str)
                        if isinstance(cmd_json, dict) and "prompt" in cmd_json:
                            coding_prompt = cmd_json["prompt"]
                    except Exception:
                        coding_prompt = t.get("description", user_prompt)
                elif "freebuff" in t.get("command", "").lower():
                    is_coding = True
                    coding_prompt = t.get("description", user_prompt)
                
                if is_coding:
                    import shlex
                    escaped_prompt = shlex.quote(coding_prompt)
                    new_tasks.append({
                        "id": t.get("id", "auto_agent_pipeline"),
                        "description": f"Execute multi-agent dev pipeline: {t.get('description', 'Build/Modify code')}",
                        "worker_type": "cmd",
                        "command": f"python experiments/auto-agent/opencode/orchestrator.py -y {escaped_prompt}"
                    })
                else:
                    new_tasks.append(t)
            
            parsed_plan["tasks"] = new_tasks
            
            # If any coding task was routed, inject the pipeline explanation into reasoning if not already there
            has_coding_task = any(t.get("id") == "auto_agent_pipeline" for t in new_tasks)
            if has_coding_task:
                pipeline_note = (
                    "I will plan the task, send to coder, and coder after creating the task sends "
                    "it to the approver (Kimi K2.7 Code) for final approval."
                )
                if "reasoning" in parsed_plan and isinstance(parsed_plan["reasoning"], str):
                    if "Reviewer" not in parsed_plan["reasoning"] and "approver" not in parsed_plan["reasoning"].lower():
                        parsed_plan["reasoning"] = pipeline_note + "\n\nOriginal reasoning: " + parsed_plan["reasoning"]
                else:
                    parsed_plan["reasoning"] = pipeline_note

        return parsed_plan

    def _clean_and_parse_json(self, raw_str: str) -> Dict[str, Any]:
        """
        Cleans JSON strings enclosed in markdown tags and parses into python dict.
        """
        cleaned = raw_str.strip()
        # Remove ```json ... ``` markdown envelopes if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()
        try:
            return json.loads(cleaned)
        except Exception as e:
            db.log("orchestrator", "ERROR", f"Failed to parse orchestrator JSON: {e}. Raw content: {raw_str}")
            # Try to regex extract anything between outer { }
            match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass
            
            # Fallback: Treat unparsed plain text response as a conversational answer
            db.log("orchestrator", "INFO", "Treating raw unparsed response text as a conversational reply.")
            return {
                "is_conversational": True,
                "response": raw_str.strip(),
                "project_name": None,
                "reasoning": "",
                "tasks": []
            }

# Global orchestrator instance
orchestrator = OpenRouterOrchestrator()
