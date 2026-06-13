import os
from pathlib import Path
from configs.config import config

class ProjectResolver:
    def __init__(self):
        self.projects_config = config.projects

    def resolve(self, name: str) -> str:
        """
        Resolves a project name/alias to an absolute directory path.
        Returns the path string if resolved, or None.
        """
        if not name:
            return None

        # 1. Direct configuration match
        if name in self.projects_config:
            path_str = self.projects_config[name].get("path")
            if path_str and os.path.exists(path_str):
                return path_str

        # 2. Case-insensitive configuration match
        name_lower = name.lower()
        for k, v in self.projects_config.items():
            if k.lower() == name_lower:
                path_str = v.get("path")
                if path_str and os.path.exists(path_str):
                    return path_str

        # 3. Dynamic lookup inside /Users/sanim/Downloads/sunny/Python/AIML
        # since it's the root parent of user projects
        search_root = Path("/Users/sanim/Downloads/sunny/Python/AIML")
        if search_root.exists():
            for child in search_root.iterdir():
                if child.is_dir():
                    # Check direct name match
                    if child.name.lower() == name_lower:
                        return str(child.resolve())
                    # Check inside Pybankers
                    if child.name == "Pybankers":
                        for subchild in child.iterdir():
                            if subchild.is_dir() and subchild.name.lower() == name_lower:
                                return str(subchild.resolve())
                    # Check inside Pygames
                    if child.name == "Pygames":
                        for subchild in child.iterdir():
                            if subchild.is_dir() and subchild.name.lower() == name_lower:
                                return str(subchild.resolve())

        # Return None if not found
        return None

    def get_all_projects(self):
        """Returns all configured projects with resolved paths."""
        resolved = {}
        for name in self.projects_config:
            path = self.resolve(name)
            if path:
                resolved[name] = path
        return resolved

# Global project resolver
project_resolver = ProjectResolver()
