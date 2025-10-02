from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from app.schemas.schemas import DocumentResponse
from app.core.security import get_current_vendor
from app.core.database import supabase
from typing import List
import os
from datetime import datetime
import uuid

router = APIRouter()

SUPABASE_STORAGE_BUCKET = "vendor-documents"  # Change this to your bucket name

def validate_file(file: UploadFile):
    """Validate file size and type"""
    # Define allowed types
    ALLOWED_TYPES = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
    MAX_FILE_SIZE = 104857600  # 100MB
    
    # Check file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_TYPES)}"
        )

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    application_id: str = Form(...),
    form_number: int = Form(...),
    document_type: str = Form(...),
    related_entity_id: str = Form(None),
    file: UploadFile = File(...),
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Upload a document for a specific form using Supabase Storage
    
    For Form 1: document_type should be 'contract' or 'invoice'
                related_entity_id should be the completed project ID
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
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", form_number)\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Cannot upload documents."
        )
    
    # Validate file
    validate_file(file)
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Check file size
    if file_size > 104857600:  # 100MB
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of 100MB"
        )
    
    # Generate unique storage path
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = f"applications/{application_id}/form_{form_number}/{document_type}/{unique_filename}"
    
    # Upload to Supabase Storage
    try:
        response = supabase.storage\
            .from_(SUPABASE_STORAGE_BUCKET)\
            .upload(
                file=file_content,
                path=storage_path,
                file_options={
                    "cache-control": "3600",
                    "upsert": "false",
                    "content-type": file.content_type
                }
            )
        
        # Get public URL
        file_url = supabase.storage\
            .from_(SUPABASE_STORAGE_BUCKET)\
            .get_public_url(storage_path)
        
    except Exception as e:
        print(f"Supabase storage error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # Save document metadata to database
    doc_data = {
        "application_id": application_id,
        "form_number": form_number,
        "related_entity_id": related_entity_id,
        "document_type": document_type,
        "file_name": file.filename,
        "file_size": file_size,
        "file_type": file.content_type,
        "s3_bucket": SUPABASE_STORAGE_BUCKET,
        "s3_key": storage_path,
        "s3_url": file_url
    }
    
    db_response = supabase.table("document_uploads")\
        .insert(doc_data)\
        .execute()
    
    if not db_response.data or len(db_response.data) == 0:
        # Cleanup Supabase Storage if database insert fails
        try:
            supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([storage_path])
        except:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save document metadata"
        )
    
    return db_response.data[0]

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Get document metadata
    """
    vendor_id = current_vendor["id"]
    
    # Get document with application check
    doc_response = supabase.table("document_uploads")\
        .select("*, vendor_applications!inner(vendor_id)")\
        .eq("id", document_id)\
        .execute()
    
    if not doc_response.data or len(doc_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc = doc_response.data[0]
    
    # Verify vendor owns the application
    if doc["vendor_applications"]["vendor_id"] != vendor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Remove the nested vendor_applications key
    doc.pop("vendor_applications", None)
    
    return doc

@router.get("/form/{application_id}/{form_number}", response_model=List[DocumentResponse])
async def get_form_documents(
    application_id: str,
    form_number: int,
    related_entity_id: str = None,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Get all documents for a specific form
    Optionally filter by related_entity_id (e.g., specific project in Form 1)
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
    
    # Build query
    query = supabase.table("document_uploads")\
        .select("*")\
        .eq("application_id", application_id)\
        .eq("form_number", form_number)
    
    if related_entity_id:
        query = query.eq("related_entity_id", related_entity_id)
    
    response = query.order("uploaded_at", desc=True).execute()
    
    return response.data

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Delete a document
    """
    vendor_id = current_vendor["id"]
    
    # Get document with application check
    doc_response = supabase.table("document_uploads")\
        .select("*, vendor_applications!inner(vendor_id)")\
        .eq("id", document_id)\
        .execute()
    
    if not doc_response.data or len(doc_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc = doc_response.data[0]
    
    # Verify vendor owns the application
    if doc["vendor_applications"]["vendor_id"] != vendor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if form is locked
    form_sub = supabase.table("form_submissions")\
        .select("*")\
        .eq("application_id", doc["application_id"])\
        .eq("form_number", doc["form_number"])\
        .execute()
    
    if form_sub.data and len(form_sub.data) > 0 and form_sub.data[0].get("is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is locked. Cannot delete documents."
        )
    
    # Delete from Supabase Storage
    try:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([doc["s3_key"]])
    except Exception as e:
        print(f"Warning: Could not delete from storage: {e}")
        # Continue anyway to delete from database
    
    # Delete from database
    supabase.table("document_uploads")\
        .delete()\
        .eq("id", document_id)\
        .execute()
    
    return None

@router.get("/{document_id}/download-url")
async def get_download_url(
    document_id: str,
    current_vendor: dict = Depends(get_current_vendor)
):
    """
    Generate a signed URL for downloading a document
    """
    vendor_id = current_vendor["id"]
    
    # Get document with application check
    doc_response = supabase.table("document_uploads")\
        .select("*, vendor_applications!inner(vendor_id)")\
        .eq("id", document_id)\
        .execute()
    
    if not doc_response.data or len(doc_response.data) == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc = doc_response.data[0]
    
    # Verify vendor owns the application
    if doc["vendor_applications"]["vendor_id"] != vendor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Generate signed URL (valid for 1 hour)
    try:
        signed_url = supabase.storage\
            .from_(SUPABASE_STORAGE_BUCKET)\
            .create_signed_url(doc["s3_key"], 3600)
        
        return {"download_url": signed_url['signedURL'], "expires_in": 3600}
    except Exception as e:
        print(f"Error generating signed URL: {e}")
        # Fallback to public URL
        return {"download_url": doc["s3_url"], "expires_in": None}