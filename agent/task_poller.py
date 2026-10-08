import logging
import uuid
logger = logging.getLogger("agent.task_poller")

def poll_tasks(api_client):
    """GET /agents/tasks and return pending task list."""
    resp = api_client.get("/agents/tasks")
    if resp is None:
        return []
    return resp if isinstance(resp, list) else resp.get("tasks", [])

def handle_task(task, api_client, offline_queue=None):
    """Dispatch task to correct handler based on scan_type."""
    scan_type = task.get("scan_type")
    task_id = task.get("id")
    logger.info(f"Processing task {task_id}: {scan_type}")
    
    if scan_type == "health_check":
        handle_health_check(task_id, api_client, offline_queue)
    elif scan_type == "discovery":
        handle_discovery(task, api_client, offline_queue)
    elif scan_type == "vulnerability":
        handle_vulnerability(task, api_client, offline_queue)
    else:
        # Unsupported type — mark FAILED
        api_client.post(f"/agents/tasks/{task_id}/status",
                        {"status": "FAILED",
                         "details": {"error": f"Unsupported scan_type: {scan_type}"}})
        logger.warning(f"Unsupported task type: {scan_type}")

def handle_health_check(task_id, api_client, offline_queue=None):
    """Collect system metrics and upload as health_check result."""
    import psutil
    api_client.post(f"/agents/tasks/{task_id}/status", {"status": "RUNNING"})
    metrics = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent if hasattr(psutil.disk_usage, '__call__') else None,
    }
    
    # Generate upload_id for idempotency
    upload_id = str(uuid.uuid4())
    result_payload = {
        "scan_id": task_id,
        "device_id": None,
        "upload_id": upload_id,
        "result_type": "system",
        "raw_payload": metrics
    }
    
    # Try to upload result
    result = api_client.post("/agents/results", result_payload)
    
    if result is None:
        # Upload failed - queue for retry
        if offline_queue:
            queued = offline_queue.enqueue({
                "method": "post",
                "path": "/agents/results",
                "data": result_payload
            })
            if queued:
                logger.warning(f"Result upload failed - queued for retry (upload_id: {upload_id})")
            else:
                logger.warning(f"Result upload failed - duplicate upload_id, not queuing (upload_id: {upload_id})")
        else:
            logger.warning(f"Result upload failed - no queue available (upload_id: {upload_id})")
    else:
        logger.info(f"Result uploaded successfully (upload_id: {upload_id})")
        api_client.post(f"/agents/tasks/{task_id}/status", {"status": "COMPLETED"})
        logger.info(f"Task completed: health_check ({task_id})")


def handle_discovery(task, api_client, offline_queue=None):
    """Perform network device discovery and upload results."""
    from agent.collectors.network_scanner import discover_devices

    task_id = task.get("id")
    target_scope = task.get("target_scope", "local")

    api_client.post(f"/agents/tasks/{task_id}/status", {"status": "RUNNING"})

    scan_data = discover_devices(target_scope)

    upload_id = str(uuid.uuid4())
    result_payload = {
        "scan_id": task_id,
        "device_id": None,
        "upload_id": upload_id,
        "result_type": "discovery",
        "raw_payload": scan_data,
    }

    result = api_client.post("/agents/results", result_payload)

    if result is None:
        if offline_queue:
            queued = offline_queue.enqueue({
                "method": "post",
                "path": "/agents/results",
                "data": result_payload,
            })
            if queued:
                logger.warning(f"Discovery upload failed - queued for retry (upload_id: {upload_id})")
        else:
            logger.warning(f"Discovery upload failed - no queue available (upload_id: {upload_id})")
    else:
        logger.info(f"Discovery results uploaded successfully (upload_id: {upload_id})")
        api_client.post(f"/agents/tasks/{task_id}/status", {"status": "COMPLETED"})
        logger.info(f"Task completed: discovery ({task_id})")


def handle_vulnerability(task, api_client, offline_queue=None):
    """Perform vulnerability service scan and upload results."""
    from agent.collectors.vulnerability_scanner import scan_vulnerabilities

    task_id = task.get("id")
    target_scope = task.get("target_scope") or "127.0.0.1"

    api_client.post(f"/agents/tasks/{task_id}/status", {"status": "RUNNING"})

    scan_data = scan_vulnerabilities(target_scope)

    upload_id = str(uuid.uuid4())
    result_payload = {
        "scan_id": task_id,
        "device_id": task.get("device_id"),
        "upload_id": upload_id,
        "result_type": "services",
        "raw_payload": scan_data,
    }

    result = api_client.post("/agents/results", result_payload)

    if result is None:
        if offline_queue:
            queued = offline_queue.enqueue({
                "method": "post",
                "path": "/agents/results",
                "data": result_payload,
            })
            if queued:
                logger.warning(f"Vulnerability upload failed - queued for retry (upload_id: {upload_id})")
        else:
            logger.warning(f"Vulnerability upload failed - no queue available (upload_id: {upload_id})")
    else:
        logger.info(f"Vulnerability results uploaded successfully (upload_id: {upload_id})")
        api_client.post(f"/agents/tasks/{task_id}/status", {"status": "COMPLETED"})
        logger.info(f"Task completed: vulnerability ({task_id})")

