import logging
import random
import time
from typing import Optional

import httpx

from agent.config import BACKEND_URL, AGENT_VERSION

logger = logging.getLogger("agent.api_client")

MAX_RETRY_ATTEMPTS = 3
FIRST_REQUEST_TIMEOUT = 90.0
NORMAL_TIMEOUT = 10.0
TRANSIENT_STATUS_CODES = {502, 503, 504}


class APIClient:
    def __init__(self, credential_token: Optional[str] = None):
        self._credential_token = credential_token
        self._credential_valid = True
        self._first_request_done = False

    def _timeout(self) -> float:
        return NORMAL_TIMEOUT if self._first_request_done else FIRST_REQUEST_TIMEOUT

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json", "User-Agent": f"CyberShieldAgent/{AGENT_VERSION}"}
        if self._credential_token:
            h["Authorization"] = f"Bearer {self._credential_token}"
        return h

    def _backoff(self, attempt: int) -> float:
        return min(2 * (2 ** attempt) + random.uniform(0, 1), 30)

    def _request(self, method: str, path: str, json_data: Optional[dict] = None) -> Optional[dict]:
        url = f"{BACKEND_URL}/api/v1{path}"
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                with httpx.Client(timeout=self._timeout()) as client:
                    response = client.request(method, url, json=json_data, headers=self._headers())
                self._first_request_done = True

                if response.status_code == 200 or response.status_code == 201:
                    return response.json()

                if response.status_code == 401:
                    logger.error("Agent credential rejected (401). Contact admin to rotate credential.")
                    self._credential_valid = False
                    return None

                if response.status_code == 403:
                    logger.error(f"Access denied (403) for {path}. Agent may be revoked.")
                    self._credential_valid = False
                    return None

                if response.status_code in TRANSIENT_STATUS_CODES:
                    wait = self._backoff(attempt)
                    logger.warning(f"Transient {response.status_code} on {path}, retry {attempt+1}/{MAX_RETRY_ATTEMPTS} in {wait:.1f}s")
                    time.sleep(wait)
                    continue

                if response.status_code == 404:
                    logger.warning(f"404 Not Found: {path}")
                    return None

                logger.warning(f"HTTP {response.status_code} on {path}")
                return None

            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as e:
                wait = self._backoff(attempt)
                logger.warning(f"Network error on {path} ({type(e).__name__}), retry {attempt+1}/{MAX_RETRY_ATTEMPTS} in {wait:.1f}s")
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    time.sleep(wait)
            except Exception as e:
                logger.error(f"Unexpected error on {path}: {type(e).__name__}")
                return None

        logger.error(f"Backend unreachable after {MAX_RETRY_ATTEMPTS} attempts for {path}.")
        return None

    def post(self, path: str, data: dict) -> Optional[dict]:
        return self._request("POST", path, json_data=data)

    def get(self, path: str) -> Optional[dict]:
        return self._request("GET", path)
