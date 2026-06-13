import subprocess
import os
import time
import select
import shlex
from typing import Tuple
from workers.base_worker import BaseWorker

STARTUP_CAPTURE_TIMEOUT = 15
MAIN_LOOP_SELECT_INTERVAL = 0.5
DRAIN_SELECT_INTERVAL = 0.3
DRAIN_IDLE_BREAKS = 3
POST_URL_SETTLE_DELAY = 1.0

class CommandCodeWorker(BaseWorker):
    def __init__(self):
        super().__init__("cmd")
        self._background_processes = {}
    
    def _is_background_service(self, command: str) -> bool:
        try:
            tokens = shlex.split(command)
        except ValueError:
            return False
        
        if not tokens:
            return False
        
        cmd_name = os.path.basename(tokens[0])
        
        background_indicators = [
            "tunnel_manager.py",
            "localtunnel",
            "lt",
        ]
        
        if cmd_name in background_indicators:
            return True
        
        is_python = cmd_name in ("python", "python3") or cmd_name.startswith("python")
        
        if len(tokens) >= 2 and is_python:
            script_name = os.path.basename(tokens[1])
            if script_name == "tunnel_manager.py":
                return True
        
        if len(tokens) >= 3 and is_python and tokens[1] == "-m":
            module_name = tokens[2]
            if module_name == "http.server":
                return True
        
        return False
    
    def stop_background_process(self, pid: int) -> Tuple[bool, str]:
        if pid not in self._background_processes:
            return False, f"Process {pid} not found in registry"
        
        process = self._background_processes[pid]
        try:
            os.killpg(os.getpgid(pid), 9)
            process.wait(timeout=5)
            del self._background_processes[pid]
            return True, f"Process {pid} terminated"
        except Exception as e:
            return False, f"Failed to terminate process {pid}: {e}"
    
    def execute(self, task_id: str, command: str, cwd: str = None) -> Tuple[bool, str]:
        self.log(task_id, "INFO", f"Running command: {command} (cwd: {cwd or 'default'})")
        
        # Determine working directory
        run_cwd = cwd
        if run_cwd:
            run_cwd = os.path.expanduser(run_cwd)
            if not os.path.exists(run_cwd):
                self.log(task_id, "ERROR", f"Cwd directory does not exist: {run_cwd}")
                return False, f"Directory not found: {run_cwd}"
        
        is_background_service = self._is_background_service(command)
        
        if is_background_service:
            self.log(task_id, "INFO", "Detected background service command. Running via Popen...")
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=run_cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    preexec_fn=os.setsid
                )
                
                self._background_processes[process.pid] = process
                
                output_lines = []
                start_time = time.time()
                
                while time.time() - start_time < STARTUP_CAPTURE_TIMEOUT:
                    if process.poll() is not None:
                        break
                    
                    ready, _, _ = select.select([process.stdout], [], [], MAIN_LOOP_SELECT_INTERVAL)
                    if ready:
                        line = process.stdout.readline()
                        if not line:
                            break
                        output_lines.append(line)
                        line_lower = line.lower()
                        if "url is:" in line_lower or "your url is:" in line_lower:
                            time.sleep(POST_URL_SETTLE_DELAY)
                            break
                        if "serving on" in line_lower or "listening on" in line_lower:
                            time.sleep(POST_URL_SETTLE_DELAY)
                            break
                    else:
                        time.sleep(0.1)
                
                idle_count = 0
                while idle_count < DRAIN_IDLE_BREAKS:
                    ready, _, _ = select.select([process.stdout], [], [], DRAIN_SELECT_INTERVAL)
                    if ready:
                        line = process.stdout.readline()
                        if not line:
                            break
                        output_lines.append(line)
                        idle_count = 0
                    else:
                        idle_count += 1
                
                if process.poll() is not None and process.returncode != 0:
                    output = "".join(output_lines)
                    self.log(task_id, "ERROR", f"Background service crashed with code {process.returncode}")
                    del self._background_processes[process.pid]
                    return False, f"Service crashed during startup (exit code {process.returncode}).\n\nOutput:\n{output}"
                
                output = "".join(output_lines)
                self.log(task_id, "INFO", f"Background service started successfully with PID {process.pid}.")
                return True, f"Service started in background (PID: {process.pid}).\n\nCaptured Output:\n{output}"
                
            except Exception as e:
                self.log(task_id, "ERROR", f"Background execution error: {e}")
                return False, str(e)
        
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
            return False, "Command execution timed out after 600 seconds."
        except Exception as e:
            self.log(task_id, "ERROR", f"Execution error: {e}")
            return False, str(e)
