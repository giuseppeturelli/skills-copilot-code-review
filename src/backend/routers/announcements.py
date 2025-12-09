"""
Endpoints for managing announcements in the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
from ..database import announcements_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)

class AnnouncementBase(BaseModel):
    message: str = Field(...)
    expiration_date: datetime = Field(...)
    start_date: Optional[datetime] = None

class AnnouncementCreate(AnnouncementBase):
    pass

class AnnouncementUpdate(BaseModel):
    message: Optional[str] = None
    expiration_date: Optional[datetime] = None
    start_date: Optional[datetime] = None

@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
def get_announcements(
    active: Optional[bool] = None,
    before: Optional[datetime] = None,
    after: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get all announcements, with optional filtering by active status and date range.

    - active: If true, only announcements that are currently active (between start_date and expiration_date)
    - before: Only announcements expiring before this date
    - after: Only announcements starting after this date
    """
    query = {}

    now = datetime.utcnow()
    if active:
        query["$and"] = [
            {"start_date": {"$lte": now}},
            {"expiration_date": {"$gte": now}}
        ]
    if before:
        query.setdefault("expiration_date", {})
        query["expiration_date"]["$lte"] = before
    if after:
        query.setdefault("start_date", {})
        query["start_date"]["$gte"] = after

    announcements = {}
    for doc in announcements_collection.find(query):
        ann_id = doc.pop('_id')
        announcements[str(ann_id)] = doc

    return announcements

@router.post("", response_model=Dict[str, Any], status_code=201)
@router.post("/", response_model=Dict[str, Any], status_code=201)
def create_announcement(announcement: AnnouncementCreate):
    """
    Create a new announcement.
    """
    data = announcement.dict()
    result = announcements_collection.insert_one(data)
    doc = announcements_collection.find_one({"_id": result.inserted_id})
    if not doc:
        raise HTTPException(status_code=500, detail="Failed to create announcement")
    doc_id = doc.pop('_id')
    return {str(doc_id): doc}

@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(announcement_id: str, update: AnnouncementUpdate):
    """
    Update an existing announcement.
    """
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")
    result = announcements_collection.update_one({"_id": announcement_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    doc = announcements_collection.find_one({"_id": announcement_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Announcement not found after update.")
    doc_id = doc.pop('_id')
    return {str(doc_id): doc}

@router.delete("/{announcement_id}", status_code=204)
def delete_announcement(announcement_id: str):
    """
    Delete an announcement.
    """
    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found.")
    return None
