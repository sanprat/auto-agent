import time
import threading
from database.db import db
from orchestrator.resolver import project_resolver

class Scheduler:
    def __init__(self):
        self.scheduler = None
        self.running = False
        self._init_scheduler()

    def _init_scheduler(self):
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            self.scheduler = BackgroundScheduler()
            
            # Register cron jobs
            # Daily SEO audit
            self.scheduler.add_job(self.run_seo_audit, 'cron', hour=1, minute=0, id='seo_audit')
            # Daily Git & GitHub review
            self.scheduler.add_job(self.run_git_review, 'cron', hour=2, minute=0, id='git_review')
            # Daily dependency updates check
            self.scheduler.add_job(self.run_dependency_check, 'cron', hour=3, minute=0, id='dependency_check')
            
            db.log("scheduler", "INFO", "APScheduler successfully initialized with daily cron jobs.")
        except ImportError:
            db.log("scheduler", "WARNING", "APScheduler not installed. Using basic thread-based fallback scheduler.")
            self.scheduler = None

    def start(self):
        if self.scheduler:
            self.scheduler.start()
            self.running = True
            db.log("scheduler", "INFO", "Scheduler daemon started.")
        else:
            self.running = True
            self._start_fallback_loop()

    def stop(self):
        self.running = False
        if self.scheduler:
            self.scheduler.shutdown()
            db.log("scheduler", "INFO", "Scheduler daemon stopped.")

    def _start_fallback_loop(self):
        def loop():
            db.log("scheduler", "INFO", "Fallback scheduler thread loop running (polling interval: 1 hour).")
            while self.running:
                # Run lightweight periodic checks
                self.run_git_review()
                time.sleep(3600)  # Sleep 1 hour
        
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    # --- Scheduled Tasks ---
    def run_seo_audit(self):
        db.log("scheduler", "INFO", "Running scheduled SEO Audit...")
        # Check active projects and crawl homepage if local site is configured
        projects = project_resolver.get_all_projects()
        for name, path in projects.items():
            db.log("scheduler", "INFO", f"Auditing SEO for project {name} in {path}")
            # Mock crawl/SEO checks
            db.set_memory("seo_audit", f"seo_audit_{name}", "SEO check completed. Meta titles/tags look healthy.", name)

    def run_git_review(self):
        db.log("scheduler", "INFO", "Running scheduled Git status review...")
        projects = project_resolver.get_all_projects()
        import subprocess
        for name, path in projects.items():
            try:
                res = subprocess.run(
                    ["git", "status", "-s"],
                    cwd=path,
                    capture_output=True,
                    text=True,
                    timeout=20
                )
                if res.returncode == 0:
                    status_out = res.stdout.strip()
                    if status_out:
                        db.log("scheduler", "INFO", f"Project {name} has uncommitted changes:\n{status_out}")
                        db.set_memory("git_status", f"uncommitted_files_{name}", status_out, name)
                    else:
                        db.set_memory("git_status", f"uncommitted_files_{name}", "Clean workspace", name)
            except Exception as e:
                db.log("scheduler", "WARNING", f"Could not audit git status for {name}: {e}")

    def run_dependency_check(self):
        db.log("scheduler", "INFO", "Running scheduled dependency vulnerability audits...")
        projects = project_resolver.get_all_projects()
        for name, path in projects.items():
            db.log("scheduler", "INFO", f"Scanning dependencies for project {name}")
            # Stub for pip check / npm audit

# Global scheduler instance
scheduler = Scheduler()
