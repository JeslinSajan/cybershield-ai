import json
import os
import uuid
from typing import Optional

IDENTITY_FILE = os.path.join(os.path.dirname(__file__), "agent_identity.json")


def load_identity() -> Optional[dict]:
    """Load agent identity from disk. Returns None if not enrolled yet."""
    if not os.path.exists(IDENTITY_FILE):
        return None
    try:
        with open(IDENTITY_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def save_identity(agent_id: str, credential_token: str) -> None:
    """Save agent identity to disk. Never log credential_token."""
    data = {"agent_id": agent_id, "credential_token": credential_token}
    with open(IDENTITY_FILE, "w") as f:
        json.dump(data, f, indent=2)
    # Restrict file permissions on Unix (no-op on Windows)
    try:
        os.chmod(IDENTITY_FILE, 0o600)
    except (OSError, AttributeError):
        pass
