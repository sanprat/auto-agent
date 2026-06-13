import os
import yaml
from pathlib import Path

# Locate current directory and root path
CONFIG_DIR = Path(__file__).parent.resolve()
ROOT_DIR = CONFIG_DIR.parent
DEFAULT_CONFIG_PATH = CONFIG_DIR / "config.yaml"

class Config:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.data = {}
        
        # Load from YAML if it exists
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                try:
                    self.data = yaml.safe_load(f) or {}
                except Exception as e:
                    print(f"Warning: Failed to load config YAML: {e}")
        
        # Ensure base structure
        self.data.setdefault("openrouter", {})
        self.data.setdefault("telegram", {})
        self.data.setdefault("supermemory", {})
        self.data.setdefault("database", {})
        self.data.setdefault("projects", {})
        self.data.setdefault("logging", {})

        # Environment variable overrides
        self._apply_env_overrides()

        # Resolve paths
        self._resolve_paths()

    def _apply_env_overrides(self):
        # OpenRouter overrides
        if "OPENROUTER_API_KEY" in os.environ:
            self.data["openrouter"]["api_key"] = os.environ["OPENROUTER_API_KEY"]
        if "OPENROUTER_MODEL" in os.environ:
            self.data["openrouter"]["model"] = os.environ["OPENROUTER_MODEL"]
        
        # Prioritize OpenCode if key is provided in the environment
        if "OPENCODE_API_KEY" in os.environ and os.environ["OPENCODE_API_KEY"]:
            self.data["openrouter"]["api_key"] = os.environ["OPENCODE_API_KEY"]
            self.data["openrouter"]["base_url"] = "https://opencode.ai/zen/go/v1"
            self.data["openrouter"]["model"] = "deepseek-v4-pro"
            
        # Ensure OpenCode config directory exists and auto-populate credentials
        if "OPENCODE_CONFIG_DIR" in os.environ and os.environ["OPENCODE_CONFIG_DIR"]:
            config_dir = Path(os.environ["OPENCODE_CONFIG_DIR"])
            config_dir.mkdir(parents=True, exist_ok=True)
            
            opencode_key = os.environ.get("OPENCODE_API_KEY")
            if opencode_key:
                auth_file = config_dir / "auth.json"
                if not auth_file.exists():
                    import json
                    auth_data = {
                        "opencode-go": {
                            "type": "api",
                            "key": opencode_key
                        }
                    }
                    try:
                        with open(auth_file, "w") as f:
                            json.dump(auth_data, f, indent=2)
                        print(f"Auto-populated OpenCode Go credentials at {auth_file}")
                    except Exception as e:
                        print(f"Warning: Failed to write OpenCode auth credentials: {e}")
        
        # Telegram overrides
        if "TELEGRAM_BOT_TOKEN" in os.environ:
            self.data["telegram"]["bot_token"] = os.environ["TELEGRAM_BOT_TOKEN"]
        if "TELEGRAM_CHAT_ID" in os.environ:
            self.data["telegram"]["chat_id"] = os.environ["TELEGRAM_CHAT_ID"]

        # Supermemory overrides
        if "SUPERMEMORY_API_KEY" in os.environ:
            self.data["supermemory"]["api_key"] = os.environ["SUPERMEMORY_API_KEY"]
        if "SUPERMEMORY_BASE_URL" in os.environ:
            self.data["supermemory"]["base_url"] = os.environ["SUPERMEMORY_BASE_URL"]

    def _resolve_paths(self):
        # Database SQLite Path
        db_path = self.data["database"].get("sqlite_path", "database/aios.db")
        resolved_db_path = ROOT_DIR / db_path
        resolved_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["database"]["sqlite_path"] = str(resolved_db_path)

        # Log Path
        log_path = self.data["logging"].get("file_path", "logs/aios.log")
        resolved_log_path = ROOT_DIR / log_path
        resolved_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.data["logging"]["file_path"] = str(resolved_log_path)

        # Projects - expand any user path (~) or relative paths
        projects = self.data.get("projects", {})
        for name, proj_conf in list(projects.items()):
            path_str = proj_conf.get("path")
            if path_str:
                expanded_path = os.path.expanduser(path_str)
                # If relative to workspace root, resolve it
                expanded_path = Path(expanded_path)
                if not expanded_path.is_absolute():
                    expanded_path = (ROOT_DIR / expanded_path).resolve()
                self.data["projects"][name]["path"] = str(expanded_path)

    @property
    def openrouter_api_key(self):
        key = self.data["openrouter"].get("api_key")
        if key == "YOUR_OPENROUTER_API_KEY":
            return os.environ.get("OPENROUTER_API_KEY", "")
        return key or ""

    @property
    def openrouter_model(self):
        return self.data["openrouter"].get("model", "openrouter/free")

    @property
    def openrouter_base_url(self):
        return self.data["openrouter"].get("base_url", "https://openrouter.ai/api/v1")

    @property
    def reasoning_enabled(self):
        return self.data["openrouter"].get("reasoning_enabled", True)

    @property
    def telegram_bot_token(self):
        token = self.data["telegram"].get("bot_token")
        if token == "YOUR_TELEGRAM_BOT_TOKEN":
            return os.environ.get("TELEGRAM_BOT_TOKEN", "")
        return token or ""

    @property
    def telegram_chat_id(self):
        cid = self.data["telegram"].get("chat_id")
        if cid == "YOUR_TELEGRAM_CHAT_ID":
            return os.environ.get("TELEGRAM_CHAT_ID", "")
        return cid or ""

    @property
    def supermemory_api_key(self):
        key = self.data["supermemory"].get("api_key")
        if key == "YOUR_SUPERMEMORY_API_KEY":
            return os.environ.get("SUPERMEMORY_API_KEY", "")
        return key or ""

    @property
    def supermemory_base_url(self):
        url = self.data["supermemory"].get("base_url")
        if url == "http://localhost:3000":
            return os.environ.get("SUPERMEMORY_BASE_URL", url)
        return url or ""

    @property
    def sqlite_path(self):
        return self.data["database"].get("sqlite_path")

    @property
    def projects(self):
        return self.data.get("projects", {})

    @property
    def log_level(self):
        return self.data["logging"].get("level", "INFO")

    @property
    def log_file_path(self):
        return self.data["logging"].get("file_path")

# Global configuration instance
config = Config()
