from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import ApplicationCreate, ApplicationResponse
from app.core.security import get_current_vendor
from app.core.database import supabase
from typing import List

router = APIRouter()

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    application: ApplicationCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Create a new application for a project
    """
    vendor_id = current_vendor["id"]
    
    # Check if application already exists
    existing = supabase.table("vendor_applications")\
        .select("*")\
        .eq("vendor_id", vendor_id)\
        .eq("project_id", application.project_id)\
        .execute()
    
    if existing.data and len(existing.data) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Application for this project already exists"
        )
    
    # Verify project exists and is active
    project = supabase.table("projects")\
        .select("*")\
        .eq("id", application.project_id)\
        .eq("is_active", True)\
        .execute()
    
    if not project.data or len(project.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found or inactive"
        )
    
    # Create application
    new_application = {
        "vendor_id": vendor_id,
        "project_id": application.project_id,
        "status": "draft"
    }
    
    response = supabase.table("vendor_applications")\
        .insert(new_application)\
        .execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create application"
        )
    
    result = response.data[0]
    result["project"] = project.data[0]
    
    return result

@router.get("", response_model=List[ApplicationResponse])
async def get_vendor_applications(current_vendor: dict = Depends(get_current_vendor)):
    """
    Get all applications for the current vendor
    """
    vendor_id = current_vendor["id"]
    
    # Get applications with project details
    response = supabase.table("vendor_applications")\
        .select("*, projects(*)")\
        .eq("vendor_id", vendor_id)\
        .order("created_at", desc=True)\
        .execute()
    
    # Transform the response to match our schema
    applications = []
    for app in response.data:
        app_data = {**app}
        if "projects" in app_data:
            app_data["project"] = app_data.pop("projects")
        applications.append(app_data)
    
    return applications

@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Get a specific application by ID
    """
    vendor_id = current_vendor["id"]
    
    response = supabase.table("vendor_applications")\
        .select("*, projects(*)")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not response.data or len(response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    app_data = response.data[0]
    if "projects" in app_data:
        app_data["project"] = app_data.pop("projects")
    
    return app_data

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Delete an application (only allowed if status is draft)
    """
    vendor_id = current_vendor["id"]
    
    # Check if application exists and belongs to vendor
    app_response = supabase.table("vendor_applications")\
        .select("*")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_response.data or len(app_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    application = app_response.data[0]
    
    # Only allow deletion if status is draft
    if application["status"] != "draft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete applications in draft status"
        )
    
    # Delete application (cascade will handle related records)
    supabase.table("vendor_applications")\
        .delete()\
        .eq("id", application_id)\
        .execute()
    
    return None