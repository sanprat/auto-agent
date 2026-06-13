# Dockerfile - Personal AI OS (aios)

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install git, Node.js, npm, and other essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && npm install -g opencode-ai command-code@latest \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose database and logs as persistent mounts
VOLUME ["/app/database", "/app/logs"]

# Start entrypoint
CMD ["python", "main.py"]
