from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import (
    EquipmentToolCreate, EquipmentToolUpdate, EquipmentToolResponse,
    Form7Response, FormSubmissionResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime

router = APIRouter()

# ============== FORM 7: EQUIPMENT AND TOOLS ==============

@router.get("/7/{application_id}", response_model=Form7Response)
async def get_form7_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get equipment and tools for Form 7"""
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
    
    # Get all equipment for this application
    equipment_response = supabase.table("contractor_equipment_tools")\
        .select("*")\
        .eq("application_id", application_id)\
        .order("created_at", desc=False)\
        .execute()
    
    # Get available equipment templates
    equipment_templates = supabase.table("equipment_tool_templates")\
        .select("equipment_type")\
        .eq("is_active", True)\
        .order("equipment_type")\
        .execute()
    
    available_equipment_types = [e["equipment_type"] for e in equipment_templates.data]
    
    # Get required equipment for this project
    required_equipment_response = supabase.table("project_required_equipment")\
        .select("*")\
        .eq("project_id", project_id)\
        .execute()
    
    # Get or create form submission
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 7)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        new_sub = {
            "application_id": application_id,
            "form_number": 7,
            "is_complete": False,
            "is_locked": False
        }
        form_sub = supabase.table("form_submissions")\
            .insert(new_sub)\
            .execute()
    
    return {
        "equipment": equipment_response.data,
        "available_equipment_types": available_equipment_types,
        "required_equipment": required_equipment_response.data,
        "form_submission": form_sub.data[0]
    }

@router.post("/7/{application_id}/equipment", response_model=EquipmentToolResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment_tool(
    application_id: str,
    equipment: EquipmentToolCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add a new equipment/tool entry to Form 7"""
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
        .eq("form_number", 7)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Create equipment record
    equipment_data = equipment.model_dump(exclude_unset=False)
    equipment_data["vendor_id"] = vendor_id
    equipment_data["application_id"] = application_id
    
    try:
        response = supabase.table("contractor_equipment_tools")\
            .insert(equipment_data)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create equipment record"
            )
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 7)\
            .execute()
        
        return response.data[0]
        
    except Exception as e:
        print(f"Error creating equipment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create equipment: {str(e)}"
        )

@router.put("/7/equipment/{equipment_id}", response_model=EquipmentToolResponse)
async def update_equipment_tool(
    equipment_id: str,
    equipment_update: EquipmentToolUpdate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Update equipment/tool entry"""
    vendor_id = current_vendor["id"]
    
    # Get equipment and verify ownership
    equipment_response = supabase.table("contractor_equipment_tools")\
        .select("*")\
        .eq("id", equipment_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not equipment_response.data or len(equipment_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment entry not found"
        )
    
    existing_equipment = equipment_response.data[0]
    application_id = existing_equipment["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 7)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Update equipment
    update_data = equipment_update.model_dump(exclude_unset=True)
    
    if update_data:
        response = supabase.table("contractor_equipment_tools")\
            .update(update_data)\
            .eq("id", equipment_id)\
            .execute()
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 7)\
            .execute()
        
        return response.data[0]
    else:
        return existing_equipment

@router.delete("/7/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment_tool(
    equipment_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Delete equipment/tool entry"""
    vendor_id = current_vendor["id"]
    
    # Get equipment and verify ownership
    equipment_response = supabase.table("contractor_equipment_tools")\
        .select("*")\
        .eq("id", equipment_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not equipment_response.data or len(equipment_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment entry not found"
        )
    
    existing_equipment = equipment_response.data[0]
    application_id = existing_equipment["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 7)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Delete equipment
    supabase.table("contractor_equipment_tools")\
        .delete()\
        .eq("id", equipment_id)\
        .execute()
    
    return None

@router.post("/7/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form7(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Submit Form 7 (marks as complete and locks)"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications")\
        .select("*")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_check.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if at least one equipment entry exists
    equipment = supabase.table("contractor_equipment_tools")\
        .select("id")\
        .eq("application_id", application_id)\
        .execute()
    
    if not equipment.data:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit form without any equipment entries"
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
        .eq("form_number", 7)\
        .execute()
    
    return response.data[0]