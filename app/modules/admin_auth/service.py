from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.timeutil import utc_now
from app.modules.admin_auth.models import AdminUser


def get_active_admin(db: Session, email: str) -> AdminUser | None:
    """Return an active admin whose email matches, ignoring case."""
    normalized_email = email.strip().lower()
    if not normalized_email:
        return None

    return db.scalar(
        select(AdminUser).where(
            AdminUser.email == normalized_email,
            AdminUser.is_active.is_(True),
        )
    )


def record_login(db: Session, admin: AdminUser) -> None:
    """Record a login, updating the timestamp at most once per hour."""
    now = utc_now()
    last = admin.last_login_at

    # SQLite may return a naive datetime even when timezone=True.
    if last is not None and last.tzinfo is None:
        last = last.replace(tzinfo=now.tzinfo)

    if last is None or now - last > timedelta(hours=1):
        admin.last_login_at = now
        db.commit()


def create_admin(
    db: Session,
    email: str,
    full_name: str | None = None,
) -> AdminUser:
    """Create an admin, or reactivate/update an existing account."""
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("Email must not be empty.")

    admin = db.scalar(
        select(AdminUser).where(AdminUser.email == normalized_email)
    )

    if admin:
        admin.is_active = True
        if full_name:
            admin.full_name = full_name
    else:
        admin = AdminUser(email=normalized_email, full_name=full_name)
        db.add(admin)

    db.commit()
    return admin


def deactivate_admin(db: Session, email: str) -> bool:
    """Deactivate an admin by email; return False if not found."""
    normalized_email = email.strip().lower()
    admin = db.scalar(
        select(AdminUser).where(AdminUser.email == normalized_email)
    )

    if not admin:
        return False

    admin.is_active = False
    db.commit()
    return True


def list_admins(db: Session) -> list[AdminUser]:
    """Return all admins ordered by email."""
    return list(db.scalars(select(AdminUser).order_by(AdminUser.email)))
