import time
import sys
import signal
from configs.config import config
from database.db import db
from scheduler.scheduler import scheduler
from telegram.bot import bot

def shutdown_handler(signum, frame):
    print("\nShutting down AI OS gracefully...")
    scheduler.stop()
    bot.stop()
    sys.exit(0)

def main():
    print("=========================================")
    print("     Starting Personal AI OS (aios)      ")
    print("=========================================")
    
    # 1. Initialize Signal Handlers
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # 2. Check configuration status
    db.log("system", "INFO", "System boot requested.")
    
    # Auto-index skills folder
    try:
        from pathlib import Path
        skills_dir = Path(__file__).parent / "skills"
        if skills_dir.exists():
            for skill_file in skills_dir.glob("*.md"):
                name = skill_file.stem
                with open(skill_file, "r") as f:
                    content = f.read()
                # Parse simple description from first lines of markdown
                desc = "Custom markdown skill"
                for line in content.splitlines():
                    if line.startswith("#"):
                        desc = line.replace("#", "").strip()
                        break
                db.set_skill(name, content, desc)
            db.log("system", "INFO", "Skills library indexed and loaded.")
    except Exception as e:
        db.log("system", "WARNING", f"Failed auto-indexing skills: {e}")

    if not config.openrouter_api_key or config.openrouter_api_key == "YOUR_OPENROUTER_API_KEY":
        db.log("system", "WARNING", "OpenRouter API Key not set. Orchestrator will run in offline fallback mode.")
    if not config.telegram_bot_token or config.telegram_bot_token == "YOUR_TELEGRAM_BOT_TOKEN":
        db.log("system", "WARNING", "Telegram Bot Token not set. Starting local terminal prompt shell interface.")

    # 3. Start scheduler background jobs
    scheduler.start()

    # 4. Start Telegram bot
    bot.start()

    # 5. Keep main process alive
    print("AI OS initialized. Keep running...")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
