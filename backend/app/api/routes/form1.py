from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import (
    CompletedProjectCreate, CompletedProjectUpdate, CompletedProjectResponse,
    Form1Response, FormSubmissionResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime

router = APIRouter()

# ============== FORM 1: COMPLETED PROJECTS ==============

@router.get("/1/{application_id}", response_model=Form1Response)
async def get_form1_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get all completed projects for Form 1 of an application"""
    vendor_id = current_vendor["id"]
    
    # Verify application belongs to vendor
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
    
    # Get all completed projects for this application
    projects_response = supabase.table("contractor_completed_projects")\
        .select("*")\
        .eq("application_id", application_id)\
        .order("created_at", desc=False)\
        .execute()
    
    # Get documents for each project
    projects_with_docs = []
    for project in projects_response.data:
        docs_response = supabase.table("document_uploads")\
            .select("*")\
            .eq("related_entity_id", project["id"])\
            .eq("form_number", 1)\
            .execute()
        
        project["documents"] = docs_response.data
        projects_with_docs.append(project)
    
    # Get or create form submission record
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 1)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        # Create form submission record
        new_sub = {
            "application_id": application_id,
            "form_number": 1,
            "is_complete": False,
            "is_locked": False
        }
        form_sub = supabase.table("form_submissions")\
            .insert(new_sub)\
            .execute()
    
    return {
        "projects": projects_with_docs,
        "form_submission": form_sub.data[0]
    }

@router.post("/1/{application_id}/projects", response_model=CompletedProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_completed_project(
    application_id: str,
    project: CompletedProjectCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add a new completed project to Form 1 (auto-save)"""
    vendor_id = current_vendor["id"]
    
    # Verify application belongs to vendor and is not locked
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
        .eq("form_number", 1)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Create project
    project_data = project.model_dump(exclude_unset=False)
    project_data["vendor_id"] = vendor_id
    project_data["application_id"] = application_id
    
    # Convert dates to strings for Supabase
    if project_data.get("contract_signing_date"):
        project_data["contract_signing_date"] = str(project_data["contract_signing_date"])
    if project_data.get("contract_start_date"):
        project_data["contract_start_date"] = str(project_data["contract_start_date"])
    if project_data.get("contract_completion_date"):
        project_data["contract_completion_date"] = str(project_data["contract_completion_date"])
    
    # Convert Decimal to float for Supabase
    if project_data.get("contract_value_sar") is not None:
        project_data["contract_value_sar"] = float(project_data["contract_value_sar"])
    
    try:
        response = supabase.table("contractor_completed_projects")\
            .insert(project_data)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project"
            )
        
        # Update form submission last_saved_at
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 1)\
            .execute()
        
        result = response.data[0]
        result["documents"] = []
        return result
        
    except Exception as e:
        print(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.put("/1/projects/{project_id}", response_model=CompletedProjectResponse)
async def update_completed_project(
    project_id: str,
    project_update: CompletedProjectUpdate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Update a completed project (auto-save)"""
    vendor_id = current_vendor["id"]
    
    # Get project and verify ownership
    project_response = supabase.table("contractor_completed_projects")\
        .select("*")\
        .eq("id", project_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not project_response.data or len(project_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    existing_project = project_response.data[0]
    application_id = existing_project["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 1)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Update project with only provided fields
    update_data = project_update.model_dump(exclude_unset=True)
    
    # Convert dates to strings
    if "contract_signing_date" in update_data and update_data["contract_signing_date"]:
        update_data["contract_signing_date"] = str(update_data["contract_signing_date"])
    if "contract_start_date" in update_data and update_data["contract_start_date"]:
        update_data["contract_start_date"] = str(update_data["contract_start_date"])
    if "contract_completion_date" in update_data and update_data["contract_completion_date"]:
        update_data["contract_completion_date"] = str(update_data["contract_completion_date"])
    
    # Convert Decimal to float
    if "contract_value_sar" in update_data and update_data["contract_value_sar"] is not None:
        update_data["contract_value_sar"] = float(update_data["contract_value_sar"])
    
    if update_data:
        response = supabase.table("contractor_completed_projects")\
            .update(update_data)\
            .eq("id", project_id)\
            .execute()
        
        # Update form submission last_saved_at
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 1)\
            .execute()
        
        result = response.data[0]
    else:
        result = existing_project
    
    # Get documents
    docs_response = supabase.table("document_uploads")\
        .select("*")\
        .eq("related_entity_id", project_id)\
        .eq("form_number", 1)\
        .execute()
    
    result["documents"] = docs_response.data
    return result

@router.delete("/1/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_completed_project(
    project_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Delete a completed project from Form 1"""
    vendor_id = current_vendor["id"]
    
    # Get project and verify ownership
    project_response = supabase.table("contractor_completed_projects")\
        .select("*")\
        .eq("id", project_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not project_response.data or len(project_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    existing_project = project_response.data[0]
    application_id = existing_project["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 1)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Delete project (documents will be handled separately)
    supabase.table("contractor_completed_projects")\
        .delete()\
        .eq("id", project_id)\
        .execute()
    
    return None

@router.post("/1/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form1(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Submit Form 1 (marks as complete and locks)"""
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
    
    # Check if at least one project exists
    projects = supabase.table("contractor_completed_projects")\
        .select("id")\
        .eq("application_id", application_id)\
        .execute()
    
    if not projects.data or len(projects.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit form without any completed projects"
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
        .eq("form_number", 1)\
        .execute()
    
    return response.data[0]