"""
CyberShield Agent — main entry point.

This agent collects system health metrics and sends them to the
CyberShield backend every HEARTBEAT_INTERVAL seconds.

IMPORTANT: This is NOT an AI agent. It is a Python monitoring script.
"""

import logging
import sys
import time

from agent import config
from agent.api_client import APIClient
from agent.enrollment import enroll
from agent.heartbeat import send_heartbeat
from agent.identity import load_identity, save_identity

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("agent.main")


def main():
    logger.info("CyberShield Agent starting...")
    logger.info(f"Backend: {config.BACKEND_URL}")

    # Load or perform enrollment
    identity = load_identity()
    if identity:
        logger.info(f"Loaded existing identity. Agent ID: {identity['agent_id']}")
    else:
        logger.info("No identity found. Starting enrollment...")
        identity = enroll(APIClient(credential_token=None))
        if identity is None:
            logger.error("Enrollment failed. Exiting.")
            sys.exit(1)
        save_identity(identity["agent_id"], identity["credential_token"])
        logger.info(f"Identity saved. Agent ID: {identity['agent_id']}")

    # Create authenticated API client
    api_client = APIClient(credential_token=identity["credential_token"])

    logger.info(f"Starting heartbeat loop (interval: {config.HEARTBEAT_INTERVAL}s)")
    while True:
        success = send_heartbeat(api_client, identity["agent_id"])

        if not api_client._credential_valid:
            logger.error("Credential rejected — contact admin to revoke and re-enroll.")
            sys.exit(1)

        time.sleep(config.HEARTBEAT_INTERVAL)


if __name__ == "__main__":
    main()
