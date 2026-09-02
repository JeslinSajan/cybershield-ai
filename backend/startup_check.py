"""
CyberShield AI - Startup Diagnostic Script
Run this on Render to diagnose startup failures:
  python startup_check.py
"""
import sys
import os

print("=" * 60)
print("CyberShield AI - Startup Diagnostic")
print("=" * 60)
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print()

# Check critical environment variables
print("--- Environment Variables ---")
db_url = os.getenv("DATABASE_URL", "NOT SET")
# Mask password for safety
if db_url != "NOT SET" and "@" in db_url:
    parts = db_url.split("@")
    masked = parts[0].split("://")[0] + "://***:***@" + parts[1]
    print(f"DATABASE_URL: {masked}")
else:
    print(f"DATABASE_URL: {db_url}")

print(f"ENVIRONMENT:  {os.getenv('ENVIRONMENT', 'NOT SET')}")
print(f"LOG_LEVEL:    {os.getenv('LOG_LEVEL', 'NOT SET')}")
print(f"DEBUG:        {os.getenv('DEBUG', 'NOT SET')}")
print()

# Check imports one by one
print("--- Import Checks ---")
checks = [
    ("fastapi", "fastapi"),
    ("pydantic", "pydantic"),
    ("pydantic_settings", "pydantic_settings"),
    ("sqlalchemy", "sqlalchemy"),
    ("psycopg", "psycopg"),
    ("app.core.config", "app.core.config"),
    ("app.core.logging", "app.core.logging"),
    ("app.core.exceptions", "app.core.exceptions"),
    ("app.core.database", "app.core.database"),
    ("app.schemas", "app.schemas"),
    ("app.api.v1.router", "app.api.v1.router"),
    ("app.main", "app.main"),
]

all_ok = True
for label, module in checks:
    try:
        __import__(module)
        print(f"  [OK]  {label}")
    except Exception as e:
        print(f"  [FAIL] {label}: {type(e).__name__}: {e}")
        all_ok = False

print()
if all_ok:
    print("All imports succeeded. App should start correctly.")
else:
    print("Import failures detected above. Fix these before starting the app.")

print("=" * 60)
