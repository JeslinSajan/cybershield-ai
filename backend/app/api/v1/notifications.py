"""
Notifications router — Phase 21 implementation.

Allows authenticated users of all roles to view, count, and mark notifications as read.
Notifications are triggered when High/Critical severity security incidents occur.
"""

import uuid
from datetime import datetime
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_any_authenticated_user
from app.models.system import Notification
from app.models.user import User

router = APIRouter()


class NotificationResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    alert_id: Optional[uuid.UUID] = None
    notification_type: str
    channel: str
    title: str
    body: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    unread_count: int


@router.get("/", response_model=List[NotificationResponse], summary="List notifications")
async def list_notifications(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
    is_read: Optional[bool] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """
    List notifications for current user's organization.
    Permitted roles: Administrator, Security Analyst, Viewer.
    """
    query = db.query(Notification).filter(Notification.organization_id == current_user.organization_id)

    # Filter for user or broadcast notifications
    query = query.filter(
        (Notification.user_id == current_user.id) | (Notification.user_id == None)
    )

    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return notifications


@router.get("/unread-count", response_model=UnreadCountResponse, summary="Get unread notification count")
async def get_unread_count(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return count of unread notifications for current user."""
    count = (
        db.query(Notification)
        .filter(
            Notification.organization_id == current_user.organization_id,
            (Notification.user_id == current_user.id) | (Notification.user_id == None),
            Notification.is_read == False,
        )
        .count()
    )
    return UnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse, summary="Mark notification as read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Mark a specific notification as read."""
    notif = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.organization_id == current_user.organization_id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Notification '{notification_id}' was not found.",
                    "details": [],
                }
            },
        )

    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.post("/mark-all-read", summary="Mark all notifications as read")
async def mark_all_notifications_read(
    current_user: Annotated[User, Depends(get_any_authenticated_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Mark all unread notifications for current user as read."""
    db.query(Notification).filter(
        Notification.organization_id == current_user.organization_id,
        (Notification.user_id == current_user.id) | (Notification.user_id == None),
        Notification.is_read == False,
    ).update({"is_read": True}, synchronize_session=False)

    db.commit()
    return {"message": "All notifications marked as read."}
