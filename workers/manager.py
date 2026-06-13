from typing import Tuple
from workers.cmd_worker import CommandCodeWorker
from workers.browser_worker import BrowserWorker
from database.db import db

class WorkerManager:
    def __init__(self):
        # Register workers
        self.workers = {
            "cmd": CommandCodeWorker(),
            "browser": BrowserWorker()
        }

    def execute_task(self, task_id: str, worker_type: str, command: str, cwd: str = None) -> Tuple[bool, str]:
        """
        Loads the matching worker type and runs the command/payload.
        Supports fallback execution routes.
        """
        # Clean worker type
        w_type = worker_type.strip().lower()
            
        worker = self.workers.get(w_type)
        if not worker:
            db.log(task_id, "WARNING", f"Worker type '{worker_type}' not found. Defaulting to CommandCodeWorker.")
            worker = self.workers["cmd"]
            
        try:
            # Update state to running
            db.update_task(task_id, status="running")
            
            # Execute
            success, output = worker.execute(task_id, command, cwd)
            
            # Update final task status
            status = "completed" if success else "failed"
            db.update_task(task_id, status=status, output=output)
            
            return success, output
            
        except Exception as e:
            db.log(task_id, "ERROR", f"Worker Manager error: {e}")
            db.update_task(task_id, status="failed", error_message=str(e))
            return False, str(e)

# Global worker manager instance
worker_manager = WorkerManager()
