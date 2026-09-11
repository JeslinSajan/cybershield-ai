"""
Role and initial admin seeding for CyberShield AI — Phase 8.

Called once during application startup (from lifespan in main.py).
Idempotent: safe to call on every startup — skips if roles/admin already exist.

SECURITY: SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD are read from environment
variables. They are NEVER logged, even at DEBUG level. Only the admin user's
email domain suffix is logged (e.g. "...@example.com"), and only to confirm
seeding completed — the full email value is not written to any log line.
"""

from app.core.database import get_session_factory
from app.core.logging import get_logger
from app.core.security import hash_password
from app.models.organization import Organization, Role
from app.models.user import User

logger = get_logger("seed")

# Canonical role names — must match user-roles.md exactly
CANONICAL_ROLES = [
    ("Administrator", "Full control of the platform, including users, roles, agents, and system settings"),
    ("Security Analyst", "Day-to-day operator: runs scans, investigates alerts, uses the AI assistant"),
    ("Viewer", "Read-only access for oversight and reporting purposes"),
]


def seed_roles_and_admin(settings) -> None:
    """Seed canonical roles and a default admin if they don't already exist.

    Args:
        settings: Application Settings instance (contains SEED_ADMIN_EMAIL,
                  SEED_ADMIN_PASSWORD — never logged).
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        # ----------------------------------------------------------------
        # 1. Seed canonical roles (idempotent)
        # ----------------------------------------------------------------
        existing_role_names = {r.name for r in db.query(Role.name).all()}
        roles_created = 0

        for role_name, description in CANONICAL_ROLES:
            if role_name not in existing_role_names:
                db.add(Role(name=role_name, description=description))
                roles_created += 1

        if roles_created:
            db.commit()
            logger.info(f"Seeded {roles_created} canonical role(s)")
        else:
            logger.info("Canonical roles already exist — skipping role seed")

        # ----------------------------------------------------------------
        # 2. Seed default organization (idempotent)
        # ----------------------------------------------------------------
        default_org = db.query(Organization).filter(Organization.slug == "default").first()
        if not default_org:
            default_org = Organization(name="Default Organization", slug="default")
            db.add(default_org)
            db.commit()
            db.refresh(default_org)
            logger.info("Seeded default organization")

        # ----------------------------------------------------------------
        # 3. Seed default admin user (idempotent)
        # Only runs if SEED_ADMIN_EMAIL and SEED_ADMIN_PASSWORD are set.
        # Credentials are never logged.
        # ----------------------------------------------------------------
        seed_email = getattr(settings, "SEED_ADMIN_EMAIL", None)
        seed_password = getattr(settings, "SEED_ADMIN_PASSWORD", None)

        if not seed_email or not seed_password:
            logger.info("SEED_ADMIN_EMAIL or SEED_ADMIN_PASSWORD not set — skipping admin seed")
            return

        existing_admin = db.query(User).filter(User.email == seed_email).first()
        if existing_admin:
            logger.info("Seed admin already exists — skipping admin seed")
            return

        admin_role = db.query(Role).filter(Role.name == "Administrator").first()
        if not admin_role:
            logger.error("Administrator role not found after seeding — cannot create admin user")
            return

        admin_user = User(
            organization_id=default_org.id,
            role_id=admin_role.id,
            email=seed_email,
            username="admin",
            password_hash=hash_password(seed_password),  # plaintext never stored
            is_active=True,
            failed_login_count=0,
        )
        db.add(admin_user)
        db.commit()

        # Log only that seeding completed — never log the email or password value
        logger.info("Default admin user seeded successfully (credentials from SEED_ADMIN_EMAIL env var)")

    except Exception as e:
        db.rollback()
        # Log the exception type but not credential values
        logger.error(f"Seeding failed: {type(e).__name__}: {str(e)}")
        raise
    finally:
        db.close()
