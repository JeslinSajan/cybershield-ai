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
from agent.offline_queue import OfflineQueue
from agent.task_poller import poll_tasks, handle_task

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

    # Initialize offline queue
    offline_queue = OfflineQueue(queue_dir=".")
    logger.info(f"Offline queue initialized with {len(offline_queue)} items")

    logger.info(f"Starting loop (heartbeat: {config.HEARTBEAT_INTERVAL}s, tasks: {config.TASK_POLL_INTERVAL}s)")
    
    last_heartbeat = 0
    last_task_poll = 0
    last_queue_drain = 0
    QUEUE_DRAIN_INTERVAL = 60  # Try to drain queue every 60 seconds
    
    while True:
        now = time.time()
        
        # Heartbeat
        if now - last_heartbeat >= config.HEARTBEAT_INTERVAL:
            send_heartbeat(api_client, identity["agent_id"])
            if not api_client._credential_valid:
                logger.error("Credential rejected — contact admin to revoke and re-enroll.")
                sys.exit(1)
            last_heartbeat = time.time()
            
        # Queue drain - attempt to send queued results
        if now - last_queue_drain >= QUEUE_DRAIN_INTERVAL:
            if not offline_queue.is_empty:
                logger.info("Attempting to drain offline queue...")
                drained = offline_queue.drain(api_client)
                if drained > 0:
                    logger.info(f"Drained {drained} items from queue")
            last_queue_drain = time.time()
            
        # Tasks
        if now - last_task_poll >= config.TASK_POLL_INTERVAL:
            tasks = poll_tasks(api_client)
            for task in tasks:
                handle_task(task, api_client, offline_queue)
            if not api_client._credential_valid:
                logger.error("Credential rejected — contact admin to revoke and re-enroll.")
                sys.exit(1)
            last_task_poll = time.time()
            
        time.sleep(1)


if __name__ == "__main__":
    main()
