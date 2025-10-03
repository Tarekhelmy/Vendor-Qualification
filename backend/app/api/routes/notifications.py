from fastapi import APIRouter, HTTPException, status, Depends
from app.core.security import get_current_vendor
from app.core.database import supabase
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.schemas import NotificationCreate, NotificationResponse

router = APIRouter()

@router.get("", response_model=List[NotificationResponse])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get notifications for the current vendor"""
    vendor_id = current_vendor["id"]
    
    query = supabase.table("notifications")\
        .select("*")\
        .eq("vendor_id", vendor_id)
    
    if unread_only:
        query = query.eq("is_read", False)
    
    response = query.order("created_at", desc=True).limit(limit).execute()
    return response.data


@router.post("/create", response_model=NotificationResponse)
async def create_notification(notification: NotificationCreate):
    """Create a notification (admin only - add authentication later)"""
    
    notification_data = notification.model_dump()
    notification_data["created_by_admin"] = True
    
    response = supabase.table("notifications").insert(notification_data).execute()
    
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create notification")
    
    return response.data[0]

@router.get("/unread-count")
async def get_unread_count(current_vendor: dict = Depends(get_current_vendor)):
    """Get count of unread notifications"""
    vendor_id = current_vendor["id"]
    
    response = supabase.table("notifications")\
        .select("id", count="exact")\
        .eq("vendor_id", vendor_id)\
        .eq("is_read", False)\
        .execute()
    
    return {"count": response.count}

@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Mark a notification as read"""
    vendor_id = current_vendor["id"]
    
    response = supabase.table("notifications")\
        .update({"is_read": True, "read_at": datetime.utcnow().isoformat()})\
        .eq("id", notification_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return response.data[0]

@router.put("/mark-all-read")
async def mark_all_read(current_vendor: dict = Depends(get_current_vendor)):
    """Mark all notifications as read"""
    vendor_id = current_vendor["id"]
    
    response = supabase.table("notifications")\
        .update({"is_read": True, "read_at": datetime.utcnow().isoformat()})\
        .eq("vendor_id", vendor_id)\
        .eq("is_read", False)\
        .execute()
    
    return {"message": "All notifications marked as read", "count": len(response.data)}

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Delete a notification"""
    vendor_id = current_vendor["id"]
    
    supabase.table("notifications")\
        .delete()\
        .eq("id", notification_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    return None