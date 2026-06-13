from database.db import db
from configs.config import config

# Try to import Supermemory SDK
try:
    from supermemory import Supermemory
    HAS_SUPERMEMORY = True
except ImportError:
    HAS_SUPERMEMORY = False

class MemoryManager:
    def __init__(self):
        self.db = db
        self.supermemory_client = None
        self._init_supermemory()

    def _init_supermemory(self):
        if HAS_SUPERMEMORY and config.supermemory_api_key:
            try:
                api_key = config.supermemory_api_key
                base_url = config.supermemory_base_url
                
                kwargs = {"api_key": api_key}
                if base_url:
                    kwargs["base_url"] = base_url
                    
                self.supermemory_client = Supermemory(**kwargs)
                self.db.log("memory", "INFO", f"Supermemory AI client initialized successfully. Endpoint: {base_url or 'default cloud'}")
            except Exception as e:
                self.db.log("memory", "WARNING", f"Failed to initialize Supermemory client: {e}")
        elif not HAS_SUPERMEMORY and config.supermemory_api_key:
            self.db.log("memory", "WARNING", "Supermemory configured but 'supermemory' python SDK is not installed.")

    def store_short_term_task(self, task_id, description, project_name=None, directory=None, worker_type=None, plan=None):
        """Stores standard task context for short-term memory."""
        self.db.create_task(
            task_id=task_id, 
            description=description, 
            project_name=project_name, 
            directory=directory, 
            worker_type=worker_type, 
            plan=plan
        )

    def update_short_term_task(self, task_id, status=None, finished_at=None, output=None, verification_status=None, error_message=None, plan=None):
        """Updates task state."""
        self.db.update_task(
            task_id=task_id,
            status=status,
            finished_at=finished_at,
            output=output,
            verification_status=verification_status,
            error_message=error_message,
            plan=plan
        )

    def log_task_event(self, task_id, level, message):
        """Records executing tasks logs."""
        self.db.log(task_id, level, message)

    def add_conversation(self, role, content, telegram_msg_id=None, reasoning_details=None):
        """Stores user/assistant conversation history in short-term buffer."""
        self.db.add_message(
            role=role, 
            content=content, 
            telegram_msg_id=telegram_msg_id, 
            reasoning_details=reasoning_details
        )

    def get_conversation_history(self, limit=15):
        """Retrieves conversational messages."""
        return self.db.get_conversation_history(limit)

    def store_long_term_memory(self, tag, key, value, project_name=None):
        """
        Stores key-value pairs representing learned workflows, 
        project configurations, or preferences.
        """
        # Save locally
        self.db.set_memory(tag=tag, key=key, value=value, project_name=project_name)
        
        # Sync to Supermemory if active
        if self.supermemory_client:
            try:
                content_str = f"[{tag}] {key}: {value}"
                container_tag = project_name if project_name else "global"
                self.supermemory_client.add(content=content_str, container_tag=container_tag)
                self.db.log("memory", "INFO", f"Long term memory synced to Supermemory: {key}")
            except Exception as e:
                self.db.log("memory", "WARNING", f"Failed to sync memory to Supermemory: {e}")

    def retrieve_memories(self, query=None, tag=None, project_name=None):
        """Searches long-term memory store."""
        return self.db.search_memories(query=query, tag=tag, project_name=project_name)

    def get_project_preferences(self, project_name):
        """Retrieves config, tech stack, preferences details for a project."""
        memories = self.db.search_memories(tag="preference", project_name=project_name)
        memories += self.db.search_memories(tag="project_info", project_name=project_name)
        
        pref_dict = {}
        for mem in memories:
            pref_dict[mem["key_text"]] = mem["value_text"]
        return pref_dict

    def get_relevant_context(self, task_description, project_name=None):
        """
        Fetches context (preferences, solutions, workflows) 
        related to the current task.
        """
        context_parts = []
        
        # 1. Look for explicit project info
        if project_name:
            prefs = self.get_project_preferences(project_name)
            if prefs:
                context_parts.append(f"### Project '{project_name}' Info:")
                for k, v in prefs.items():
                    context_parts.append(f"- {k}: {v}")

        # 2. Query matches in local memories
        keywords = [w for w in task_description.lower().split() if len(w) > 3]
        matched_memories = []
        for kw in keywords[:5]: # Search by top keywords
            matched_memories.extend(self.db.search_memories(query=kw))
        
        # Deduplicate matched memories
        seen = set()
        dedup_memories = []
        for m in matched_memories:
            if m["id"] not in seen:
                seen.add(m["id"])
                dedup_memories.append(m)

        if dedup_memories:
            context_parts.append("### Relevant Local Learned Solutions:")
            for m in dedup_memories:
                context_parts.append(f"- [{m['tag']}] {m['key_text']}: {m['value_text']}")
                
        # 3. Query Supermemory client if active
        if self.supermemory_client:
            try:
                container_tag = project_name if project_name else "global"
                sm_results = self.supermemory_client.profile(
                    container_tag=container_tag,
                    q=task_description
                )
                if sm_results:
                    context_parts.append(f"### Supermemory context ({container_tag}):")
                    context_parts.append(str(sm_results))
            except Exception as e:
                self.db.log("memory", "WARNING", f"Failed to retrieve Supermemory context: {e}")
                
        return "\n".join(context_parts) if context_parts else "No relevant memory context found."

# Global memory manager instance
memory_manager = MemoryManager()
