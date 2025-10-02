from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from app.schemas.schemas import (
    QuestionnaireResponseCreate, QuestionnaireResponseUpdate,
    QuestionnaireResponseDetail, Form8Response, FormSubmissionResponse,
    QuestionnaireAttachmentResponse
)
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime
import os
import uuid

router = APIRouter()

SUPABASE_STORAGE_BUCKET = "vendor-documents"

# ============== FORM 8: QUESTIONNAIRE ==============

@router.get("/8/{application_id}", response_model=Form8Response)
async def get_form8_data(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Get questionnaire for Form 8"""
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
    
    # Get questions for this project
    questions_response = supabase.table("questionnaire_questions")\
        .select("*")\
        .eq("project_id", project_id)\
        .eq("is_active", True)\
        .order("question_number")\
        .execute()
    
    # Get responses for this application
    responses_response = supabase.table("questionnaire_responses")\
        .select("*")\
        .eq("application_id", application_id)\
        .execute()
    
    # Get attachments for each response
    detailed_responses = []
    for response in responses_response.data:
        attachments = supabase.table("questionnaire_attachments")\
            .select("*")\
            .eq("response_id", response["id"])\
            .execute()
        
        response["attachments"] = attachments.data
        detailed_responses.append(response)
    
    # Get or create form submission
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 8)\
        .execute()
    
    if not form_sub.data or len(form_sub.data) == 0:
        new_sub = {
            "application_id": application_id,
            "form_number": 8,
            "is_complete": False,
            "is_locked": False
        }
        form_sub = supabase.table("form_submissions")\
            .insert(new_sub)\
            .execute()
    
    return {
        "questions": questions_response.data,
        "responses": detailed_responses,
        "form_submission": form_sub.data[0]
    }

@router.post("/8/{application_id}/responses", response_model=QuestionnaireResponseDetail, status_code=status.HTTP_201_CREATED)
async def create_questionnaire_response(
    application_id: str,
    response: QuestionnaireResponseCreate,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Create or update questionnaire response"""
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
        .eq("form_number", 8)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(status_code=403, detail="Form is locked")
    
    # Check if response already exists
    existing = supabase.table("questionnaire_responses")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("question_id", response.question_id)\
        .execute()
    
    if existing.data:
        # Update existing response
        update_data = {"answer_text": response.answer_text}
        result = supabase.table("questionnaire_responses")\
            .update(update_data)\
            .eq("id", existing.data[0]["id"])\
            .execute()
        
        response_id = existing.data[0]["id"]
    else:
        # Create new response
        response_data = response.model_dump()
        response_data["vendor_id"] = vendor_id
        response_data["application_id"] = application_id
        
        result = supabase.table("questionnaire_responses")\
            .insert(response_data)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create response")
        
        response_id = result.data[0]["id"]
    
    # Update form submission
    supabase.table("form_submissions")\
        .update({"last_saved_at": datetime.utcnow().isoformat()})\
        .eq("application_id", application_id)\
        .eq("form_number", 8)\
        .execute()
    
    # Get attachments
    attachments = supabase.table("questionnaire_attachments")\
        .select("*")\
        .eq("response_id", response_id)\
        .execute()
    
    response_data = result.data[0] if result.data else existing.data[0]
    response_data["attachments"] = attachments.data
    
    return response_data

@router.post("/8/responses/{response_id}/attachments", response_model=QuestionnaireAttachmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_questionnaire_attachment(
    response_id: str,
    file: UploadFile = File(...),
    current_vendor: dict = Depends(get_current_vendor)
):
    """Upload attachment for questionnaire response"""
    vendor_id = current_vendor["id"]
    
    # Verify response ownership
    response_check = supabase.table("questionnaire_responses")\
        .select("application_id")\
        .eq("id", response_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not response_check.data:
        raise HTTPException(status_code=404, detail="Response not found")
    
    application_id = response_check.data[0]["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 8)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(status_code=403, detail="Form is locked")
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check file size
    if file_size > 104857600:  # 100MB
        raise HTTPException(status_code=400, detail="File size exceeds 100MB")
    
    # Generate unique storage path
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = f"applications/{application_id}/form_8/{response_id}/{unique_filename}"
    
    # Upload to Supabase Storage
    try:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            file=file_content,
            path=storage_path,
            file_options={"cache-control": "3600", "upsert": "false", "content-type": file.content_type}
        )
        
        file_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(storage_path)
    except Exception as e:
        print(f"Storage error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # Save attachment metadata
    attachment_data = {
        "response_id": response_id,
        "document_type": "questionnaire_attachment",
        "file_name": file.filename,
        "file_size": file_size,
        "file_type": file.content_type,
        "s3_bucket": SUPABASE_STORAGE_BUCKET,
        "s3_key": storage_path,
        "s3_url": file_url
    }
    
    result = supabase.table("questionnaire_attachments").insert(attachment_data).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to save attachment metadata")
    
    return result.data[0]

@router.delete("/8/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_questionnaire_attachment(
    attachment_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Delete questionnaire attachment"""
    vendor_id = current_vendor["id"]
    
    # Get attachment with ownership check
    attachment = supabase.table("questionnaire_attachments")\
        .select("*, questionnaire_responses!inner(vendor_id, application_id)")\
        .eq("id", attachment_id)\
        .execute()
    
    if not attachment.data or attachment.data[0]["questionnaire_responses"]["vendor_id"] != vendor_id:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    application_id = attachment.data[0]["questionnaire_responses"]["application_id"]
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", 8)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(status_code=403, detail="Form is locked")
    
    # Delete from storage
    try:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([attachment.data[0]["s3_key"]])
    except Exception as e:
        print(f"Warning: Could not delete from storage: {e}")
    
    # Delete from database
    supabase.table("questionnaire_attachments").delete().eq("id", attachment_id).execute()
    
    return None
@router.post("/8/{application_id}/submit", response_model=FormSubmissionResponse)
async def submit_form8(
    application_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """Submit Form 8 (marks as complete and locks)"""
    vendor_id = current_vendor["id"]
    
    # Verify application
    app_check = supabase.table("vendor_applications")\
        .select("*, projects!inner(id)")\
        .eq("id", application_id)\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    if not app_check.data:
        raise HTTPException(status_code=404, detail="Application not found")
    
    project_id = app_check.data[0]["projects"]["id"]
    
    # Get all questions for this project
    questions = supabase.table("questionnaire_questions")\
        .select("*")\
        .eq("project_id", project_id)\
        .eq("is_active", True)\
        .execute()
    
    # Get all responses
    responses = supabase.table("questionnaire_responses")\
        .select("*")\
        .eq("application_id", application_id)\
        .execute()
    
    # Only check if all questions are answered (no attachment requirement)
    answered_question_ids = {r["question_id"] for r in responses.data}
    all_question_ids = {q["id"] for q in questions.data}
    
    if answered_question_ids != all_question_ids:
        raise HTTPException(
            status_code=400,
            detail="All questions must be answered before submission"
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
        .eq("form_number", 8)\
        .execute()
    
    return response.data[0]