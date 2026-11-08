from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.services.notification_service import queue_emergency_notifications
from app.schemas.notification import NotificationQueueResponse
router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notification Delivery"],
)
from app.schemas.notification import EmergencyNotificationStatusResponse
from app.services.notification_status_service import (
    get_emergency_notification_status,
)
@router.post(
    "/emergencies/{emergency_id}/queue",
    response_model=NotificationQueueResponse,
)
def queue_notifications(
    emergency_id: UUID,
    current_user=Depends(get_current_user),
):
    try:
        return queue_emergency_notifications(
            emergency_id=emergency_id,
            user_id=UUID(str(current_user.user_id)),
        )

    except PermissionError:
        raise HTTPException(
            status_code=404,
            detail="Emergency record not found.",
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        )
        
        
@router.get(
    "/emergencies/{emergency_id}/status",
    response_model=EmergencyNotificationStatusResponse,
)
def get_notification_status(
    emergency_id: UUID,
    current_user=Depends(get_current_user),
):
    try:
        return get_emergency_notification_status(
            emergency_id=emergency_id,
            user_id=UUID(str(current_user.user_id)),
        )

    except PermissionError:
        raise HTTPException(
            status_code=404,
            detail="Emergency record not found.",
        )