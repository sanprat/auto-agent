import subprocess
import os
from typing import Tuple
from workers.base_worker import BaseWorker

class CommandCodeWorker(BaseWorker):
    def __init__(self):
        super().__init__("cmd")

    def execute(self, task_id: str, command: str, cwd: str = None) -> Tuple[bool, str]:
        self.log(task_id, "INFO", f"Running command: {command} (cwd: {cwd or 'default'})")
        
        # Determine working directory
        run_cwd = cwd
        if run_cwd:
            run_cwd = os.path.expanduser(run_cwd)
            if not os.path.exists(run_cwd):
                self.log(task_id, "ERROR", f"Cwd directory does not exist: {run_cwd}")
                return False, f"Directory not found: {run_cwd}"
        
        # Execute shell command
        try:
            # Run in shell to support piping/redirection if requested
            process = subprocess.run(
                command,
                shell=True,
                cwd=run_cwd,
                capture_output=True,
                text=True,
                timeout=600  # Prevent infinite hangs
            )
            
            output = f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
            
            if process.returncode == 0:
                self.log(task_id, "INFO", "Command completed successfully.")
                return True, output
            else:
                self.log(task_id, "ERROR", f"Command failed with code {process.returncode}")
                return False, output

        except subprocess.TimeoutExpired as te:
            self.log(task_id, "ERROR", f"Command timed out: {te}")
            return False, "Command execution timed out after 120 seconds."
        except Exception as e:
            self.log(task_id, "ERROR", f"Execution error: {e}")
            return False, str(e)
