"""
Rate Limiter configuration using slowapi (Phase 22).

Configures rate limiting keyed by client IP address.
Default limits are empty; specific limits are applied per-endpoint (e.g., POST /auth/login).
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=[])
