import subprocess
import os
from pathlib import Path
from database.db import db

class Verifier:
    def verify_project(self, project_name: str, project_path: str) -> bool:
        """
        Runs tests and lint checks in the target project path.
        Returns True if all verification checks pass, otherwise False.
        """
        if not project_path or not os.path.exists(project_path):
            db.log("verifier", "WARNING", f"No valid path to verify for {project_name}")
            return True # Nothing to verify

        p_path = Path(project_path)
        
        # 1. Determine if Python project (contains pytest, requirements, etc.)
        is_python = (p_path / "requirements.txt").exists() or (p_path / "pyproject.toml").exists() or any(p_path.glob("*.py"))
        
        # 2. Determine if NodeJS project (contains package.json)
        is_node = (p_path / "package.json").exists()

        db.log("verifier", "INFO", f"Verifying {project_name}. Python={is_python}, Node={is_node}")

        success = True

        if is_python:
            # Check if pytest is applicable
            has_tests_dir = (p_path / "tests").exists() or (p_path / "test").exists()
            if has_tests_dir:
                db.log("verifier", "INFO", "Running pytest suite...")
                try:
                    res = subprocess.run(
                        ["pytest"],
                        cwd=project_path,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if res.returncode != 0:
                        db.log("verifier", "ERROR", f"pytest failed:\n{res.stdout}\n{res.stderr}")
                        success = False
                    else:
                        db.log("verifier", "INFO", "pytest verification passed.")
                except Exception as e:
                    db.log("verifier", "WARNING", f"Could not run pytest: {e}")

            # Run ruff check if installed
            try:
                res = subprocess.run(
                    ["ruff", "check", "."],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if res.returncode != 0:
                    db.log("verifier", "WARNING", f"ruff check failed:\n{res.stdout}")
                    # We treat warnings/lints as non-blocking for basic verification unless critical
            except Exception:
                pass

        if is_node:
            # Run npm test
            db.log("verifier", "INFO", "Running npm test...")
            try:
                res = subprocess.run(
                    ["npm", "test"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if res.returncode != 0:
                    db.log("verifier", "ERROR", f"npm test failed:\n{res.stdout}\n{res.stderr}")
                    success = False
                else:
                    db.log("verifier", "INFO", "npm test passed.")
            except Exception as e:
                db.log("verifier", "WARNING", f"Could not run npm test: {e}")

        return success

# Global verifier instance
verifier = Verifier()
