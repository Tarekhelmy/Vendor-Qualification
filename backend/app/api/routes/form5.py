from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import (
    PersonnelResumeCreate, PersonnelResumeUpdate, PersonnelResumeResponse,
    EducationItem, EducationResponse, WorkExperienceItem, WorkExperienceResponse,
    Form5Response, FormSubmissionResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime

router = APIRouter()

# ============== FORM 5: PERSONNEL RESUMES ==============

@router.get("/5/{application_id}", response_model=Form5Response)
async def get_form5_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get personnel resumes for Form 5 (based on Form 4 personnel)"""
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
    
    # Get all personnel from Form 4
    personnel_response = supabase.table("management_personnel")\
        .select("id, full_name, position, nationality")\
        .eq("application_id", application_id)\
        .order("created_at")\
        .execute()
    
    # Get all resumes for this application
    resumes_response = supabase.table("personnel_resumes")\
        .select("*")\
        .eq("application_id", application_id)\
        .execute()
    
    resumes_map = {r["personnel_id"]: r for r in resumes_response.data}
    
    # Format personnel list with resume status
    personnel_list = []
    for person in personnel_response.data:
        has_resume = person["id"] in resumes_map
        personnel_list.append({
            "id": person["id"],
            "full_name": person["full_name"],
            "position": person["position"],
            "nationality": person.get("nationality"),
            "has_resume": has_resume,
            "resume_id": resumes_map[person["id"]]["id"] if has_resume else None
        })
    
    # Get detailed resumes with education and work experience
    detailed_resumes = []
    for resume in resumes_response.data:
        # Get education
        education = supabase.table("personnel_education")\
            .select("*")\
            .eq("resume_id", resume["id"])\
            .order("year_from", desc=True)\
            .execute()
        
        # Get work experience
        work_exp = supabase.table("personnel_work_experience")\
            .select("*")\
            .eq("resume_id", resume["id"])\
            .order("date_from", desc=True)\
            .execute()
        
        resume["education"] = education.data
        resume["work_experience"] = work_exp.data
        detailed_resumes.append(resume)
    
    # Get or create form submission
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 5)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        new_sub = {
            "application_id": application_id,
            "form_number": 5,
            "is_complete": False,
            "is_locked": False
        }
        form_sub = supabase.table("form_submissions")\
            .insert(new_sub)\
            .execute()
    
    return {
        "personnel_list": personnel_list,
        "resumes": detailed_resumes,
        "form_submission": form_sub.data[0]
    }

@router.post("/5/{application_id}/resumes", response_model=PersonnelResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_personnel_resume(
    application_id: str,
    resume: PersonnelResumeCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Create a resume for a personnel from Form 4"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications")\
        .select("*")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_check.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 5)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(status_code=403, detail="Form is locked")
    
    # Verify personnel exists and belongs to this application
    personnel = supabase.table("management_personnel")\
        .select("*")\
        .eq("id", resume.personnel_id)\
        .eq("application_id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not personnel.data:
        raise HTTPException(status_code=404, detail="Personnel not found")
    
    # Check if resume already exists
    existing = supabase.table("personnel_resumes")\
        .select("id")\
        .eq("personnel_id", resume.personnel_id)\
        .execute()
    
    if existing.data:
        raise HTTPException(status_code=400, detail="Resume already exists for this personnel")
    
    # Create resume
    resume_data = resume.model_dump(exclude_unset=False)
    resume_data["application_id"] = application_id
    
    if resume_data.get("date_of_birth"):
        resume_data["date_of_birth"] = str(resume_data["date_of_birth"])
    
    try:
        response = supabase.table("personnel_resumes").insert(resume_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create resume")
        
        # Update form submission
        supabase.table("form_submissions")\
            .update({"last_saved_at": datetime.utcnow().isoformat()})\
            .eq("application_id", application_id)\
            .eq("form_number", 5)\
            .execute()
        
        result = response.data[0]
        result["education"] = []
        result["work_experience"] = []
        return result
        
    except Exception as e:
        print(f"Error creating resume: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create resume: {str(e)}")

@router.put("/5/resumes/{resume_id}", response_model=PersonnelResumeResponse)
async def update_personnel_resume(
    resume_id: str,
    resume_update: PersonnelResumeUpdate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Update personnel resume"""
    vendor_id = current_vendor["id"]
    
    # Get resume and verify ownership
    resume_response = supabase.table("personnel_resumes")\
        .select("*, management_personnel!inner(vendor_id)")\
        .eq("id", resume_id)\
        .execute()
    
    if not resume_response.data or resume_response.data[0]["management_personnel"]["vendor_id"] != vendor_id:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    existing_resume = resume_response.data[0]
    application_id = existing_resume["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 5)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(status_code=403, detail="Form is locked")
    
    # Update resume
    update_data = resume_update.model_dump(exclude_unset=True)
    
    if "date_of_birth" in update_data and update_data["date_of_birth"]:
        update_data["date_of_birth"] = str(update_data["date_of_birth"])
    
    if update_data:
        response = supabase.table("personnel_resumes").update(update_data).eq("id", resume_id).execute()
        result = response.data[0]
    else:
        result = existing_resume
    
    # Get related data
    education = supabase.table("personnel_education").select("*").eq("resume_id", resume_id).order("year_from", desc=True).execute()
    work_exp = supabase.table("personnel_work_experience").select("*").eq("resume_id", resume_id).order("date_from", desc=True).execute()
    
    result["education"] = education.data
    result["work_experience"] = work_exp.data
    result.pop("management_personnel", None)
    
    return result

@router.delete("/5/resumes/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personnel_resume(
    resume_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Delete personnel resume"""
    vendor_id = current_vendor["id"]
    
    # Get resume and verify ownership
    resume_response = supabase.table("personnel_resumes")\
        .select("*, management_personnel!inner(vendor_id, application_id)")\
        .eq("id", resume_id)\
        .execute()
    
    if not resume_response.data or resume_response.data[0]["management_personnel"]["vendor_id"] != vendor_id:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    application_id = resume_response.data[0]["management_personnel"]["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 5)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(status_code=403, detail="Form is locked")
    
    # Delete resume (cascade will delete education and work experience)
    supabase.table("personnel_resumes").delete().eq("id", resume_id).execute()
    return None

# Education endpoints
@router.post("/5/resumes/{resume_id}/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def add_education(
    resume_id: str,
    education: EducationItem,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add education to resume"""
    data = {"resume_id": resume_id, **education.model_dump()}
    response = supabase.table("personnel_education").insert(data).execute()
    return response.data[0]

@router.delete("/5/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(education_id: str, current_vendor: dict = Depends(get_current_vendor)):
    """Delete education entry"""
    supabase.table("personnel_education").delete().eq("id", education_id).execute()
    return None

# Work experience endpoints
@router.post("/5/resumes/{resume_id}/work-experience", response_model=WorkExperienceResponse, status_code=status.HTTP_201_CREATED)
async def add_work_experience(
    resume_id: str,
    work_exp: WorkExperienceItem,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Add work experience to resume"""
    data = work_exp.model_dump()
    if data.get("date_from"):
        data["date_from"] = str(data["date_from"])
    if data.get("date_to"):
        data["date_to"] = str(data["date_to"])
    data["resume_id"] = resume_id
    
    response = supabase.table("personnel_work_experience").insert(data).execute()
    return response.data[0]

@router.delete("/5/work-experience/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_work_experience(experience_id: str, current_vendor: dict = Depends(get_current_vendor)):
    """Delete work experience entry"""
    supabase.table("personnel_work_experience").delete().eq("id", experience_id).execute()
    return None

@router.post("/5/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form5(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Submit Form 5"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications").select("*").eq("id", application_id).eq("vendor_id", vendor_id).execute()
    if not app_check.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Check if at least one resume exists
    resumes = supabase.table("personnel_resumes").select("id").eq("application_id", application_id).execute()
    if not resumes.data:
        raise HTTPException(status_code=400, detail="Cannot submit form without any resumes")
    
    # Update form submission
    update_data = {
        "is_complete": True,
        "is_locked": True,
        "submitted_at": datetime.utcnow().isoformat(),
        "last_saved_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("form_submissions").update(update_data).eq("application_id", application_id).eq("form_number", 5).execute()
    return response.data[0]