import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
ENROLLMENT_TOKEN = os.getenv("ENROLLMENT_TOKEN", "")
AGENT_NAME = os.getenv("AGENT_NAME", "cybershield-agent")
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
TASK_POLL_INTERVAL = int(os.getenv("TASK_POLL_INTERVAL", "30"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
AGENT_VERSION = "1.0.0"
