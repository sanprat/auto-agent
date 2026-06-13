-- SQL Schema for Personal AI OS (aios) Database

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    plan TEXT,
    status TEXT DEFAULT 'pending', -- pending, running, completed, failed
    project_name TEXT,
    directory TEXT,
    worker_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    output TEXT,
    verification_status TEXT DEFAULT 'unverified', -- unverified, verified, failed
    error_message TEXT
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    log_level TEXT NOT NULL,
    message TEXT NOT NULL,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_msg_id INTEGER,
    role TEXT NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    reasoning_details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL, -- preference, project_info, previous_solution, workflow
    project_name TEXT,
    key_text TEXT UNIQUE NOT NULL,
    value_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skills (
    name TEXT PRIMARY KEY,
    description TEXT,
    content TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
