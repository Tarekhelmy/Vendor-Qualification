from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import (
    ProjectProfileCreate, ProjectProfileUpdate, ProjectProfileResponse,
    PersonnelItem, PersonnelResponse, EquipmentItem, EquipmentResponse,
    MaterialItem, MaterialResponse, SubcontractorItem, SubcontractorResponse,
    Form3Response, FormSubmissionResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime

router = APIRouter()

# ============== FORM 3: PROJECT PROFILES ==============

@router.get("/3/{application_id}", response_model=Form3Response)
async def get_form3_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get project profiles for Form 3. Shows ongoing projects from Form 2 and their profiles"""
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
    """Create a profile for an ongoing project from Form 2"""
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
    """Update a project profile"""
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
    """Delete a project profile"""
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