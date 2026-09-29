import logging
from typing import Optional

from agent.api_client import APIClient
from agent.config import AGENT_NAME, ENROLLMENT_TOKEN, BACKEND_URL
import socket

logger = logging.getLogger("agent.enrollment")


def enroll(api_client: APIClient) -> Optional[dict]:
    """
    Register agent using the enrollment token.
    Returns: {"agent_id": str, "credential_token": str}
    Never logs the credential token.
    """
    if not ENROLLMENT_TOKEN:
        logger.error("ENROLLMENT_TOKEN is not set in .env. Cannot enroll.")
        return None

    hostname = socket.gethostname()
    payload = {
        "enrollment_token": ENROLLMENT_TOKEN,
        "name": AGENT_NAME,
        "hostname": hostname,
        "version": "1.0.0",
    }

    # Use unauthenticated client for registration
    unauth_client = APIClient(credential_token=None)
    result = unauth_client.post("/agents/register", payload)

    if result is None:
        logger.error("Enrollment failed. Check ENROLLMENT_TOKEN and BACKEND_URL.")
        return None

    agent_id = result.get("id")
    credential = result.get("credential", {})
    credential_token = credential.get("token")

    if not agent_id or not credential_token:
        logger.error("Enrollment response missing agent ID or credential.")
        return None

    logger.info(f"Agent enrolled successfully. ID: {agent_id}")
    # Never log credential_token
    return {"agent_id": agent_id, "credential_token": credential_token}
