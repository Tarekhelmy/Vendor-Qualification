from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import (
    ManpowerCreate, ManpowerUpdate, ManpowerResponse,
    Form6Response, FormSubmissionResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime

router = APIRouter()

# ============== FORM 6: SKILLED AND UNSKILLED MANPOWER ==============

@router.get("/6/{application_id}", response_model=Form6Response)
async def get_form6_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get skilled and unskilled manpower for Form 6"""
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
    
    # Get all manpower for this application
    manpower_response = supabase.table("skilled_unskilled_manpower")\
        .select("*")\
        .eq("application_id", application_id)\
        .order("created_at", desc=False)\
        .execute()
    
    # Get available craft templates
    crafts_response = supabase.table("manpower_craft_templates")\
        .select("craft_name")\
        .eq("is_active", True)\
        .order("craft_name")\
        .execute()
    
    available_crafts = [c["craft_name"] for c in crafts_response.data]
    
    # Get required crafts for this project
    required_crafts_response = supabase.table("project_required_crafts")\
        .select("*")\
        .eq("project_id", project_id)\
        .execute()
    
    # Get or create form submission
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 6)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        new_sub = {
            "application_id": application_id,
            "form_number": 6,
            "is_complete": False,
            "is_locked": False
        }
        form_sub = supabase.table("form_submissions")\
            .insert(new_sub)\
            .execute()
    
    return {
        "manpower": manpower_response.data,
        "available_crafts": available_crafts,
        "required_crafts": required_crafts_response.data,
        "form_submission": form_sub.data[0]
    }

@router.post("/6/{application_id}/manpower", response_model=ManpowerResponse, status_code=status.HTTP_201_CREATED)
async def create_manpower(
    application_id: str,
    manpower: ManpowerCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add a new manpower entry to Form 6"""
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
        .eq("form_number", 6)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Create manpower record
    manpower_data = manpower.model_dump(exclude_unset=False)
    manpower_data["vendor_id"] = vendor_id
    manpower_data["application_id"] = application_id
    
    try:
        response = supabase.table("skilled_unskilled_manpower")\
            .insert(manpower_data)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create manpower record"
            )
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 6)\
            .execute()
        
        return response.data[0]
        
    except Exception as e:
        print(f"Error creating manpower: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create manpower: {str(e)}"
        )

@router.put("/6/manpower/{manpower_id}", response_model=ManpowerResponse)
async def update_manpower(
    manpower_id: str,
    manpower_update: ManpowerUpdate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Update manpower entry"""
    vendor_id = current_vendor["id"]
    
    # Get manpower and verify ownership
    manpower_response = supabase.table("skilled_unskilled_manpower")\
        .select("*")\
        .eq("id", manpower_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not manpower_response.data or len(manpower_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manpower entry not found"
        )
    
    existing_manpower = manpower_response.data[0]
    application_id = existing_manpower["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 6)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Update manpower
    update_data = manpower_update.model_dump(exclude_unset=True)
    
    if update_data:
        response = supabase.table("skilled_unskilled_manpower")\
            .update(update_data)\
            .eq("id", manpower_id)\
            .execute()
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 6)\
            .execute()
        
        return response.data[0]
    else:
        return existing_manpower

@router.delete("/6/manpower/{manpower_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_manpower(
    manpower_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Delete manpower entry"""
    vendor_id = current_vendor["id"]
    
    # Get manpower and verify ownership
    manpower_response = supabase.table("skilled_unskilled_manpower")\
        .select("*")\
        .eq("id", manpower_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not manpower_response.data or len(manpower_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manpower entry not found"
        )
    
    existing_manpower = manpower_response.data[0]
    application_id = existing_manpower["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 6)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Delete manpower
    supabase.table("skilled_unskilled_manpower")\
        .delete()\
        .eq("id", manpower_id)\
        .execute()
    
    return None

@router.post("/6/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form6(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Submit Form 6 (marks as complete and locks)"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications")\
        .select("*")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_check.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if at least one manpower entry exists
    manpower = supabase.table("skilled_unskilled_manpower")\
        .select("id")\
        .eq("application_id", application_id)\
        .execute()
    
    if not manpower.data:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit form without any manpower entries"
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
        .eq("form_number", 6)\
        .execute()
    
    return response.data[0]