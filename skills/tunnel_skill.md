# Expose Local Web Projects to Mobile/Public Browser (localtunnel)

This skill describes how to host a local web directory (like Pygames or Sahas frontend views) and expose it using localtunnel so the user can interact with it on their phone browser from outside.

## When to use:
- The user requests: "expose the web game", "give me a link to my project", "open a tunnel for Pygames", "let me view/play it on my phone".

## Workflow Steps:

1. **Resolve project path:** Use the project resolver to locate the absolute directory path (e.g. `/Users/sanim/Downloads/sunny/Python/AIML/Pygames`).
2. **Execute tunnel manager:** Run the `workers/tunnel_manager.py` script in a background process using the `cmd` worker on the target project.
3. **Command Format:**
   ```bash
   python3 workers/tunnel_manager.py <target_directory> [port]
   ```
4. **Identify the URL:** Scans the command output logs for the line `👉 URL: https://xxxx.loca.lt`.
5. **Report:** Send the public link URL to the user via Telegram so they can click and load it.
