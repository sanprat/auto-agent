import sys
import os
import re
from typing import Tuple
from workers.base_worker import BaseWorker

class BrowserWorker(BaseWorker):
    def __init__(self):
        super().__init__("browser")

    def execute(self, task_id: str, command: str, cwd: str = None) -> Tuple[bool, str]:
        """
        Runs browser operations. 
        command format can be a simple URL (for crawl) or a python snippet that uses playwright.
        """
        # If the command starts with http:// or https://, we treat it as a crawl request
        if command.strip().startswith(("http://", "https://")):
            return self._crawl_website(task_id, command.strip())
        
        # Else, we execute the script as python playwright code
        return self._execute_playwright_script(task_id, command, cwd)

    def _crawl_website(self, task_id: str, url: str) -> Tuple[bool, str]:
        self.log(task_id, "INFO", f"Crawling URL: {url}")
        
        # Try to use BeautifulSoup + requests for a clean and fast extraction
        try:
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "header", "footer", "nav"]):
                script.decompose()
                
            # Extract main text
            text = soup.get_text()
            
            # Basic cleanup (reduce empty lines)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            cleaned_text = "\n".join(chunk for chunk in chunks if chunk)
            
            # Limit length for storage
            markdown_content = f"# Crawled Content from {url}\n\n" + cleaned_text[:8000]
            self.log(task_id, "INFO", f"Successfully crawled {url}")
            return True, markdown_content

        except Exception as e:
            self.log(task_id, "ERROR", f"Failed crawling {url} using BeautifulSoup: {e}")
            return False, f"Crawl failed: {e}"

    def _execute_playwright_script(self, task_id: str, script_code: str, cwd: str) -> Tuple[bool, str]:
        self.log(task_id, "INFO", "Executing Playwright Python script.")
        
        # Write to a temp file and execute inside opencode style
        # Inject standard playwright imports if not present
        full_code = script_code
        if "sync_playwright" not in script_code:
            full_code = (
                "from playwright.sync_api import sync_playwright\n"
                "import sys\n\n"
                "def run():\n"
                "    with sync_playwright() as p:\n"
                "        browser = p.chromium.launch(headless=True)\n"
                "        page = browser.new_page()\n"
                f"        # User script goes here\n"
                f"        {script_code.replace(chr(10), chr(10) + '        ')}\n"
                "        browser.close()\n\n"
                "if __name__ == '__main__':\n"
                "    run()\n"
            )
            
        # We can run this code via a subprocess python executor to isolate it
        run_cwd = cwd or os.getcwd()
        script_file = os.path.join(run_cwd, f"playwright_temp_{task_id}.py")
        
        try:
            with open(script_file, "w") as f:
                f.write(full_code)
                
            import subprocess
            process = subprocess.run(
                ["python3", script_file],
                cwd=run_cwd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            output = f"STDOUT:\n{process.stdout}\nSTDERR:\n{process.stderr}"
            
            if process.returncode == 0:
                self.log(task_id, "INFO", "Playwright script finished successfully.")
                return True, output
            else:
                self.log(task_id, "ERROR", f"Playwright script failed with code {process.returncode}")
                return False, output
                
        except Exception as e:
            self.log(task_id, "ERROR", f"Playwright wrapper execution error: {e}")
            return False, str(e)
        finally:
            if os.path.exists(script_file):
                try:
                    os.remove(script_file)
                except:
                    pass
