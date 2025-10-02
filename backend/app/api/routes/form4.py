from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import (
    ManagementPersonnelCreate, ManagementPersonnelUpdate, ManagementPersonnelResponse,
    Form4Response, FormSubmissionResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime
from typing import List

router = APIRouter()

# ============== FORM 4: MANAGEMENT AND SUPERVISORY PERSONNEL ==============

@router.get("/4/{application_id}", response_model=Form4Response)
async def get_form4_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get management and supervisory personnel for Form 4"""
    vendor_id = current_vendor["id"]
    
    # Verify application belongs to vendor
    app_check = supabase.table("vendor_applications")\
        .select("*, projects!inner(id)")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_check.data or len(app_check.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    project_id = app_check.data[0]["projects"]["id"]
    
    # Get all personnel for this application
    personnel_response = supabase.table("management_personnel")\
        .select("*")\
        .eq("application_id", application_id)\
        .order("created_at", desc=False)\
        .execute()
    
    # Get available position templates
    positions_response = supabase.table("position_templates")\
        .select("position_name")\
        .eq("is_active", True)\
        .order("position_name")\
        .execute()
    
    available_positions = [p["position_name"] for p in positions_response.data]
    
    # Get required positions for this project
    required_positions_response = supabase.table("project_required_positions")\
        .select("*")\
        .eq("project_id", project_id)\
        .execute()
    
    # Get or create form submission
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 4)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        new_sub = {
            "application_id": application_id,
            "form_number": 4,
            "is_complete": False,
            "is_locked": False
        }
        form_sub = supabase.table("form_submissions")\
            .insert(new_sub)\
            .execute()
    
    return {
        "personnel": personnel_response.data,
        "available_positions": available_positions,
        "required_positions": required_positions_response.data,
        "form_submission": form_sub.data[0]
    }

@router.post("/4/{application_id}/personnel", response_model=ManagementPersonnelResponse, status_code=status.HTTP_201_CREATED)
async def create_management_personnel(
    application_id: str,
    personnel: ManagementPersonnelCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add a new management/supervisory personnel to Form 4"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications")\
        .select("*")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_check.data or len(app_check.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 4)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Create personnel record
    personnel_data = personnel.model_dump(exclude_unset=False)
    personnel_data["vendor_id"] = vendor_id
    personnel_data["application_id"] = application_id
    
    try:
        response = supabase.table("management_personnel")\
            .insert(personnel_data)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create personnel record"
            )
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 4)\
            .execute()
        
        return response.data[0]
        
    except Exception as e:
        print(f"Error creating personnel: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create personnel: {str(e)}"
        )

@router.put("/4/personnel/{personnel_id}", response_model=ManagementPersonnelResponse)
async def update_management_personnel(
    personnel_id: str,
    personnel_update: ManagementPersonnelUpdate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Update management/supervisory personnel"""
    vendor_id = current_vendor["id"]
    
    # Get personnel and verify ownership
    personnel_response = supabase.table("management_personnel")\
        .select("*")\
        .eq("id", personnel_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not personnel_response.data or len(personnel_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personnel not found"
        )
    
    existing_personnel = personnel_response.data[0]
    application_id = existing_personnel["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 4)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Update personnel
    update_data = personnel_update.model_dump(exclude_unset=True)
    
    if update_data:
        response = supabase.table("management_personnel")\
            .update(update_data)\
            .eq("id", personnel_id)\
            .execute()
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 4)\
            .execute()
        
        return response.data[0]
    else:
        return existing_personnel

@router.delete("/4/personnel/{personnel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_management_personnel(
    personnel_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Delete management/supervisory personnel"""
    vendor_id = current_vendor["id"]
    
    # Get personnel and verify ownership
    personnel_response = supabase.table("management_personnel")\
        .select("*")\
        .eq("id", personnel_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not personnel_response.data or len(personnel_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personnel not found"
        )
    
    existing_personnel = personnel_response.data[0]
    application_id = existing_personnel["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 4)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Delete personnel
    supabase.table("management_personnel")\
        .delete()\
        .eq("id", personnel_id)\
        .execute()
    
    return None

@router.post("/4/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form4(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Submit Form 4 (marks as complete and locks)"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications")\
        .select("*")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_check.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if at least one personnel exists
    personnel = supabase.table("management_personnel")\
        .select("id")\
        .eq("application_id", application_id)\
        .execute()
    
    if not personnel.data:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit form without any personnel records"
        )
    
    # Update form submission
    update_data = {
        "is_complete": True,
        "is_locked": True,
        "submitted_at": datetime.utcnow().isoformat(),
        "last_saved_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("form_submissions")\
        .update(update_data)\
        .eq("application_id", application_id)\
        .eq("form_number", 4)\
        .execute()
    
    return response.data[0]