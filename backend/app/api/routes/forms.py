from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import (
    CompletedProjectCreate, CompletedProjectUpdate, CompletedProjectResponse,
    Form1Response, FormSubmitRequest, FormSubmissionResponse, Form2Response,
    OngoingProjectCreate, OngoingProjectUpdate, OngoingProjectResponse,
    DocumentResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from typing import List
from datetime import datetime

router = APIRouter()

# ============== FORM 1: COMPLETED PROJECTS ==============

@router.get("/1/{application_id}", response_model=Form1Response)
async def get_form1_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Get all completed projects for Form 1 of an application
    """
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
    """
    Add a new completed project to Form 1 (auto-save)
    """
    # ADD THESE DEBUG LINES:
    print("=" * 60)
    print("Received project data:")
    print(project)
    print("Project dict:")
    print(project.model_dump())
    print("=" * 60)
    
    # REMOVE THIS DUPLICATE DOCSTRING:
    # """
    # Add a new completed project to Form 1 (auto-save)
    # """
    
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
    
    # Create project - convert Pydantic model to dict and handle None values
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
    """
    Update a completed project (auto-save)
    """
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
    """
    Delete a completed project from Form 1
    """
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
    """
    Submit Form 1 (marks as complete and locks)
    """
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

# ============== FORM 2: ONGOING PROJECTS ==============

@router.get("/2/{application_id}", response_model=Form2Response)
async def get_form2_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Get all ongoing projects for Form 2 of an application
    """
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
    
    # Get all ongoing projects for this application
    projects_response = supabase.table("contractor_ongoing_projects")\
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
            .eq("form_number", 2)\
            .execute()
        
        project["documents"] = docs_response.data
        projects_with_docs.append(project)
    
    # Get or create form submission record
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 2)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        new_sub = {
            "application_id": application_id,
            "form_number": 2,
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

@router.post("/2/{application_id}/projects", response_model=OngoingProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_ongoing_project(
    application_id: str,
    project: OngoingProjectCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Add a new ongoing project to Form 2
    """
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
        .eq("form_number", 2)\
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
    
    # Convert dates and decimals
    if project_data.get("contract_signing_date"):
        project_data["contract_signing_date"] = str(project_data["contract_signing_date"])
    if project_data.get("contract_start_date"):
        project_data["contract_start_date"] = str(project_data["contract_start_date"])
    if project_data.get("contract_completion_date"):
        project_data["contract_completion_date"] = str(project_data["contract_completion_date"])
    
    if project_data.get("contract_value_sar") is not None:
        project_data["contract_value_sar"] = float(project_data["contract_value_sar"])
    if project_data.get("percent_completion") is not None:
        project_data["percent_completion"] = float(project_data["percent_completion"])
    if project_data.get("completed_value_sar") is not None:
        project_data["completed_value_sar"] = float(project_data["completed_value_sar"])
    
    try:
        response = supabase.table("contractor_ongoing_projects")\
            .insert(project_data)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project"
            )
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 2)\
            .execute()
        
        result = response.data[0]
        result["documents"] = []
        return result
        
    except Exception as e:
        print(f"Error creating ongoing project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.put("/2/projects/{project_id}", response_model=OngoingProjectResponse)
async def update_ongoing_project(
    project_id: str,
    project_update: OngoingProjectUpdate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Update an ongoing project
    """
    vendor_id = current_vendor["id"]
    
    # Get project and verify ownership
    project_response = supabase.table("contractor_ongoing_projects")\
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
        .eq("form_number", 2)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Update project
    update_data = project_update.model_dump(exclude_unset=True)
    
    # Convert dates and decimals
    if "contract_signing_date" in update_data and update_data["contract_signing_date"]:
        update_data["contract_signing_date"] = str(update_data["contract_signing_date"])
    if "contract_start_date" in update_data and update_data["contract_start_date"]:
        update_data["contract_start_date"] = str(update_data["contract_start_date"])
    if "contract_completion_date" in update_data and update_data["contract_completion_date"]:
        update_data["contract_completion_date"] = str(update_data["contract_completion_date"])
    
    if "contract_value_sar" in update_data and update_data["contract_value_sar"] is not None:
        update_data["contract_value_sar"] = float(update_data["contract_value_sar"])
    if "percent_completion" in update_data and update_data["percent_completion"] is not None:
        update_data["percent_completion"] = float(update_data["percent_completion"])
    if "completed_value_sar" in update_data and update_data["completed_value_sar"] is not None:
        update_data["completed_value_sar"] = float(update_data["completed_value_sar"])
    
    if update_data:
        response = supabase.table("contractor_ongoing_projects")\
            .update(update_data)\
            .eq("id", project_id)\
            .execute()
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 2)\
            .execute()
        
        result = response.data[0]
    else:
        result = existing_project
    
    # Get documents
    docs_response = supabase.table("document_uploads")\
        .select("*")\
        .eq("related_entity_id", project_id)\
        .eq("form_number", 2)\
        .execute()
    
    result["documents"] = docs_response.data
    return result

@router.delete("/2/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ongoing_project(
    project_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Delete an ongoing project from Form 2
    """
    vendor_id = current_vendor["id"]
    
    # Get project and verify ownership
    project_response = supabase.table("contractor_ongoing_projects")\
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
        .eq("form_number", 2)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Delete project
    supabase.table("contractor_ongoing_projects")\
        .delete()\
        .eq("id", project_id)\
        .execute()
    
    return None

@router.post("/2/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form2(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Submit Form 2 (marks as complete and locks)
    """
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
    projects = supabase.table("contractor_ongoing_projects")\
        .select("id")\
        .eq("application_id", application_id)\
        .execute()
    
    if not projects.data or len(projects.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot submit form without any ongoing projects"
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
        .eq("form_number", 2)\
        .execute()
    
    return response.data[0]

# ============== FORM 3: PROJECT PROFILES ==============

@router.get("/3/{application_id}", response_model=Form3Response)
async def get_form3_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Get project profiles for Form 3
    Shows ongoing projects from Form 2 and their profiles
    """
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
    
    # Get ongoing projects from Form 2
    ongoing_projects = supabase.table("contractor_ongoing_projects")\
        .select("*")\
        .eq("application_id", application_id)\
        .execute()
    
    # Get all profiles for this application
    profiles_response = supabase.table("project_profiles")\
        .select("*")\
        .eq("application_id", application_id)\
        .execute()
    
    profiles_map = {p["ongoing_project_id"]: p for p in profiles_response.data}
    
    # Format ongoing projects with profile status
    projects_with_status = []
    for project in ongoing_projects.data:
        has_profile = project["id"] in profiles_map
        projects_with_status.append({
            "id": project["id"],
            "project_field": project["project_field"],
            "contract_number": project.get("contract_number"),
            "client_name": project["client_name"],
            "project_title": project["project_title"],
            "contract_value_sar": project.get("contract_value_sar"),
            "percent_completion": project.get("percent_completion"),
            "has_profile": has_profile,
            "profile_id": profiles_map[project["id"]]["id"] if has_profile else None
        })
    
    # Get detailed profiles with related data
    detailed_profiles = []
    for profile in profiles_response.data:
        # Get personnel
        personnel = supabase.table("project_personnel")\
            .select("*")\
            .eq("project_profile_id", profile["id"])\
            .execute()
        
        # Get equipment
        equipment = supabase.table("project_equipment")\
            .select("*")\
            .eq("project_profile_id", profile["id"])\
            .execute()
        
        # Get materials
        materials = supabase.table("project_materials")\
            .select("*")\
            .eq("project_profile_id", profile["id"])\
            .execute()
        
        # Get subcontractors
        subcontractors = supabase.table("project_subcontractors")\
            .select("*")\
            .eq("project_profile_id", profile["id"])\
            .execute()
        
        profile["personnel"] = personnel.data
        profile["equipment"] = equipment.data
        profile["materials"] = materials.data
        profile["subcontractors"] = subcontractors.data
        detailed_profiles.append(profile)
    
    # Get or create form submission
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 3)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        new_sub = {
            "application_id": application_id,
            "form_number": 3,
            "is_complete": False,
            "is_locked": False
        }
        form_sub = supabase.table("form_submissions")\
            .insert(new_sub)\
            .execute()
    
    return {
        "ongoing_projects": projects_with_status,
        "profiles": detailed_profiles,
        "form_submission": form_sub.data[0]
    }

@router.post("/3/{application_id}/profiles", response_model=ProjectProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_project_profile(
    application_id: str,
    profile: ProjectProfileCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Create a profile for an ongoing project from Form 2
    """
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
        .eq("form_number", 3)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Verify ongoing project exists and belongs to this application
    ongoing_project = supabase.table("contractor_ongoing_projects")\
        .select("*")\
        .eq("id", profile.ongoing_project_id)\
        .eq("application_id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not ongoing_project.data or len(ongoing_project.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ongoing project not found or does not belong to this application"
        )
    
    # Check if profile already exists
    existing = supabase.table("project_profiles")\
        .select("id")\
        .eq("ongoing_project_id", profile.ongoing_project_id)\
        .execute()
    
    if existing.data and len(existing.data) > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists for this project"
        )
    
    # Create profile
    profile_data = profile.model_dump(exclude_unset=False)
    profile_data["vendor_id"] = vendor_id
    profile_data["application_id"] = application_id
    
    # Convert dates
    for date_field in ["contract_signed_date", "completion_date", "forecasted_completion_date"]:
        if profile_data.get(date_field):
            profile_data[date_field] = str(profile_data[date_field])
    
    # Convert decimals
    if profile_data.get("percent_completion") is not None:
        profile_data["percent_completion"] = float(profile_data["percent_completion"])
    if profile_data.get("contract_value_sar") is not None:
        profile_data["contract_value_sar"] = float(profile_data["contract_value_sar"])
    
    try:
        response = supabase.table("project_profiles")\
            .insert(profile_data)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create profile"
            )
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 3)\
            .execute()
        
        result = response.data[0]
        result["personnel"] = []
        result["equipment"] = []
        result["materials"] = []
        result["subcontractors"] = []
        return result
        
    except Exception as e:
        print(f"Error creating profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create profile: {str(e)}"
        )

@router.put("/3/profiles/{profile_id}", response_model=ProjectProfileResponse)
async def update_project_profile(
    profile_id: str,
    profile_update: ProjectProfileUpdate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Update a project profile
    """
    vendor_id = current_vendor["id"]
    
    # Get profile and verify ownership
    profile_response = supabase.table("project_profiles")\
        .select("*")\
        .eq("id", profile_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not profile_response.data or len(profile_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    existing_profile = profile_response.data[0]
    application_id = existing_profile["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 3)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Update profile
    update_data = profile_update.model_dump(exclude_unset=True)
    
    # Convert dates
    for date_field in ["contract_signed_date", "completion_date", "forecasted_completion_date"]:
        if date_field in update_data and update_data[date_field]:
            update_data[date_field] = str(update_data[date_field])
    
    # Convert decimals
    if "percent_completion" in update_data and update_data["percent_completion"] is not None:
        update_data["percent_completion"] = float(update_data["percent_completion"])
    if "contract_value_sar" in update_data and update_data["contract_value_sar"] is not None:
        update_data["contract_value_sar"] = float(update_data["contract_value_sar"])
    
    if update_data:
        response = supabase.table("project_profiles")\
            .update(update_data)\
            .eq("id", profile_id)\
            .execute()
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 3)\
            .execute()
        
        result = response.data[0]
    else:
        result = existing_profile
    
    # Get related data
    personnel = supabase.table("project_personnel").select("*").eq("project_profile_id", profile_id).execute()
    equipment = supabase.table("project_equipment").select("*").eq("project_profile_id", profile_id).execute()
    materials = supabase.table("project_materials").select("*").eq("project_profile_id", profile_id).execute()
    subcontractors = supabase.table("project_subcontractors").select("*").eq("project_profile_id", profile_id).execute()
    
    result["personnel"] = personnel.data
    result["equipment"] = equipment.data
    result["materials"] = materials.data
    result["subcontractors"] = subcontractors.data
    
    return result

@router.delete("/3/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_profile(
    profile_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Delete a project profile
    """
    vendor_id = current_vendor["id"]
    
    # Get profile and verify ownership
    profile_response = supabase.table("project_profiles")\
        .select("*")\
        .eq("id", profile_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not profile_response.data or len(profile_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    existing_profile = profile_response.data[0]
    application_id = existing_profile["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 3)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Request unlock permission to edit."
        )
    
    # Delete profile (cascade will delete related data)
    supabase.table("project_profiles")\
        .delete()\
        .eq("id", profile_id)\
        .execute()
    
    return None

# Personnel endpoints
@router.post("/3/profiles/{profile_id}/personnel", response_model=PersonnelResponse, status_code=status.HTTP_201_CREATED)
async def add_personnel(
    profile_id: str,
    personnel: PersonnelItem,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add personnel to project profile"""
    vendor_id = current_vendor["id"]
    
    # Verify profile ownership
    profile = supabase.table("project_profiles").select("application_id").eq("id", profile_id).eq("vendor_id", vendor_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    data = {"project_profile_id": profile_id, **personnel.model_dump()}
    response = supabase.table("project_personnel").insert(data).execute()
    return response.data[0]

@router.delete("/3/personnel/{personnel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personnel(personnel_id: str, current_vendor: dict = Depends(get_current_vendor)):
    """Delete personnel from project"""
    supabase.table("project_personnel").delete().eq("id", personnel_id).execute()
    return None

# Equipment endpoints
@router.post("/3/profiles/{profile_id}/equipment", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def add_equipment(
    profile_id: str,
    equipment: EquipmentItem,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add equipment to project profile"""
    vendor_id = current_vendor["id"]
    
    profile = supabase.table("project_profiles").select("application_id").eq("id", profile_id).eq("vendor_id", vendor_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    data = {"project_profile_id": profile_id, **equipment.model_dump()}
    response = supabase.table("project_equipment").insert(data).execute()
    return response.data[0]

@router.delete("/3/equipment/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(equipment_id: str, current_vendor: dict = Depends(get_current_vendor)):
    """Delete equipment from project"""
    supabase.table("project_equipment").delete().eq("id", equipment_id).execute()
    return None

# Materials endpoints
@router.post("/3/profiles/{profile_id}/materials", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
async def add_material(
    profile_id: str,
    material: MaterialItem,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add material to project profile"""
    vendor_id = current_vendor["id"]
    
    profile = supabase.table("project_profiles").select("application_id").eq("id", profile_id).eq("vendor_id", vendor_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    data = {"project_profile_id": profile_id, **material.model_dump()}
    response = supabase.table("project_materials").insert(data).execute()
    return response.data[0]

@router.delete("/3/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(material_id: str, current_vendor: dict = Depends(get_current_vendor)):
    """Delete material from project"""
    supabase.table("project_materials").delete().eq("id", material_id).execute()
    return None

# Subcontractors endpoints
@router.post("/3/profiles/{profile_id}/subcontractors", response_model=SubcontractorResponse, status_code=status.HTTP_201_CREATED)
async def add_subcontractor(
    profile_id: str,
    subcontractor: SubcontractorItem,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add subcontractor to project profile"""
    vendor_id = current_vendor["id"]
    
    profile = supabase.table("project_profiles").select("application_id").eq("id", profile_id).eq("vendor_id", vendor_id).execute()
    if not profile.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    data = subcontractor.model_dump()
    if data.get("value_sar") is not None:
        data["value_sar"] = float(data["value_sar"])
    data["project_profile_id"] = profile_id
    
    response = supabase.table("project_subcontractors").insert(data).execute()
    return response.data[0]

@router.delete("/3/subcontractors/{subcontractor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subcontractor(subcontractor_id: str, current_vendor: dict = Depends(get_current_vendor)):
    """Delete subcontractor from project"""
    supabase.table("project_subcontractors").delete().eq("id", subcontractor_id).execute()
    return None

@router.post("/3/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form3(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Submit Form 3 (marks as complete and locks)"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications").select("*").eq("id", application_id).eq("vendor_id", vendor_id).execute()
    if not app_check.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if at least one profile exists
    profiles = supabase.table("project_profiles").select("id").eq("application_id", application_id).execute()
    if not profiles.data:
        raise HTTPException(status_code=400, detail="Cannot submit form without any project profiles")
    
    # Update form submission
    update_data = {
        "is_complete": True,
        "is_locked": True,
        "submitted_at": datetime.utcnow().isoformat(),
        "last_saved_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("form_submissions").update(update_data).eq("application_id", application_id).eq("form_number", 3).execute()
    return response.data[0]