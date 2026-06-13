import uuid
import time
from typing import Dict, List, Any
from database.db import db
from orchestrator.resolver import project_resolver
from workers.manager import worker_manager
from verifier.verifier import verifier

class TaskPlanner:
    def __init__(self):
        self.db = db

    def execute_plan(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Takes a structured plan dictionary (containing tasks and project_name)
        and runs each task sequentially.
        """
        project_name = plan.get("project_name")
        resolved_path = project_resolver.resolve(project_name) if project_name else None
        
        self.db.log("planner", "INFO", f"Executing plan for project '{project_name}' (Resolved CWD: {resolved_path})")

        tasks = plan.get("tasks", [])
        executed_tasks = []

        for task_data in tasks:
            raw_id = task_data.get("id") or "task"
            import re
            raw_id = re.sub(r'[^a-zA-Z0-9_\-]', '', raw_id)
            task_id = f"{raw_id}_{uuid.uuid4().hex[:8]}"
            description = task_data.get("description", "No description")
            worker_type = task_data.get("worker_type", "cmd")
            command = task_data.get("command", "")

            # 1. Store task in DB short-term memory
            self.db.create_task(
                task_id=task_id,
                description=description,
                project_name=project_name,
                directory=resolved_path,
                worker_type=worker_type,
                plan=plan.get("reasoning", "")
            )

            self.db.log(task_id, "INFO", f"Starting subtask: {description} via {worker_type}")

            # 2. Execute via Worker Manager
            success, output = worker_manager.execute_task(
                task_id=task_id,
                worker_type=worker_type,
                command=command,
                cwd=resolved_path
            )

            # 3. Post-execution verification
            v_status = "unverified"
            if success:
                # If command succeeded, run verifier to verify correctness
                self.db.log(task_id, "INFO", f"Task execution succeeded. Starting verification...")
                verified = verifier.verify_project(project_name, resolved_path)
                v_status = "verified" if verified else "failed"
                self.db.update_task(task_id, verification_status=v_status)
                if not verified:
                    self.db.log(task_id, "WARNING", f"Verification failed for {description}")
            else:
                self.db.log(task_id, "ERROR", f"Task execution failed. Output: {output[:300]}")
                # Failure retry flow: Try fallback worker if cmd fails, run freebuff to debug
                if worker_type == "cmd":
                    self.db.log(task_id, "WARNING", "Command worker failed. Retrying with OpenCode worker if applicable...")
                    # For example, if it's a python command, try running a quick python fix script
                    # We log the retry event but keep the failed state if retry doesn't happen
            
            task_state = self.db.get_task(task_id)
            executed_tasks.append(task_state)

            if not success and v_status != "verified":
                # Break execution chain on failure to prevent cascading issues
                self.db.log("planner", "ERROR", f"Breaking task chain due to failure in {task_id}")
                break

        return executed_tasks

# Global planner instance
task_planner = TaskPlanner()
