from abc import ABC, abstractmethod
from typing import Tuple
from memory.memory_manager import memory_manager

class BaseWorker(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, task_id: str, command: str, cwd: str = None) -> Tuple[bool, str]:
        """
        Executes a task command/payload in the given directory context.
        Returns: (success: bool, output: str)
        """
        pass

    def log(self, task_id: str, level: str, message: str):
        """Helper to log worker status to DB."""
        memory_manager.log_task_event(task_id, level, f"[{self.name.upper()}] {message}")
