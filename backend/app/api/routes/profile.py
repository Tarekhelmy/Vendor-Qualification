from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from app.schemas.schemas import VendorProfileResponse, FinancialStatementResponse, LegalDocumentResponse
from app.core.security import get_current_vendor
from app.core.database import supabase
from datetime import datetime
import os
import uuid

router = APIRouter()

SUPABASE_STORAGE_BUCKET = "vendor-documents"

@router.get("/me", response_model=VendorProfileResponse)
async def get_vendor_profile(current_vendor: dict = Depends(get_current_vendor)):
    """Get vendor profile with all documents"""
    vendor_id = current_vendor["id"]
    
    # Get financial statements
    financial_statements = supabase.table("vendor_financial_statements")\
        .select("*")\
        .eq("vendor_id", vendor_id)\
        .order("year", desc=True)\
        .execute()
    
    # Get legal documents
    legal_documents = supabase.table("vendor_legal_documents")\
        .select("*")\
        .eq("vendor_id", vendor_id)\
        .execute()
    
    # Check completeness
    current_year = datetime.now().year
    required_years = list(range(current_year - 5, current_year))
    uploaded_years = {fs["year"] for fs in financial_statements.data}
    missing_years = [year for year in required_years if year not in uploaded_years]
    
    required_legal_docs = ["classification_certificate", "saudi_contractors_authority", "municipal_registration"]
    uploaded_legal_types = {doc["document_type"] for doc in legal_documents.data}
    missing_legal_docs = [doc for doc in required_legal_docs if doc not in uploaded_legal_types]
    
    missing_items = []
    if missing_years:
        missing_items.extend([f"Financial Statement {year}" for year in missing_years])
    if missing_legal_docs:
        doc_names = {
            "classification_certificate": "Classification Certificate",
            "saudi_contractors_authority": "Saudi Contractors Authority Certificate",
            "municipal_registration": "Municipal Registration Certificate"
        }
        missing_items.extend([doc_names[doc] for doc in missing_legal_docs])
    
    profile_complete = len(missing_items) == 0
    
    return {
        "vendor": current_vendor,
        "financial_statements": financial_statements.data,
        "legal_documents": legal_documents.data,
        "profile_complete": profile_complete,
        "missing_items": missing_items
    }

@router.post("/financial-statement/{year}", response_model=FinancialStatementResponse)
async def upload_financial_statement(
    year: int,
    file: UploadFile = File(...),
    current_vendor: dict = Depends(get_current_vendor)
):
    """Upload financial statement for a specific year"""
    vendor_id = current_vendor["id"]
    
    # Validate year
    current_year = datetime.now().year
    if year < current_year - 5 or year >= current_year:
        raise HTTPException(status_code=400, detail="Invalid year. Must be within last 5 years")
    
    # Read file
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > 104857600:  # 100MB
        raise HTTPException(status_code=400, detail="File size exceeds 100MB")
    
    # Generate storage path
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = f"vendors/{vendor_id}/financial/{year}/{unique_filename}"
    
    # Check if document already exists
    existing = supabase.table("vendor_financial_statements")\
        .select("*")\
        .eq("vendor_id", vendor_id)\
        .eq("year", year)\
        .execute()
    
    # Delete old file from storage if exists
    if existing.data:
        try:
            supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([existing.data[0]["s3_key"]])
        except:
            pass
    
    # Upload to storage
    try:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            file=file_content,
            path=storage_path,
            file_options={"cache-control": "3600", "upsert": "false", "content-type": file.content_type}
        )
        file_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(storage_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # Save metadata
    doc_data = {
        "vendor_id": vendor_id,
        "year": year,
        "file_name": file.filename,
        "file_size": file_size,
        "file_type": file.content_type,
        "s3_bucket": SUPABASE_STORAGE_BUCKET,
        "s3_key": storage_path,
        "s3_url": file_url
    }
    
    if existing.data:
        # Update existing
        result = supabase.table("vendor_financial_statements")\
            .update(doc_data)\
            .eq("id", existing.data[0]["id"])\
            .execute()
    else:
        # Insert new
        result = supabase.table("vendor_financial_statements")\
            .insert(doc_data)\
            .execute()
    
    return result.data[0]

@router.delete("/financial-statement/{year}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_financial_statement(year: int, current_vendor: dict = Depends(get_current_vendor)):
    """Delete financial statement"""
    vendor_id = current_vendor["id"]
    
    doc = supabase.table("vendor_financial_statements")\
        .select("*")\
        .eq("vendor_id", vendor_id)\
        .eq("year", year)\
        .execute()
    
    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from storage
    try:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([doc.data[0]["s3_key"]])
    except:
        pass
    
    # Delete from database
    supabase.table("vendor_financial_statements").delete().eq("id", doc.data[0]["id"]).execute()
    return None

@router.post("/legal-document/{document_type}", response_model=LegalDocumentResponse)
async def upload_legal_document(
    document_type: str,
    file: UploadFile = File(...),
    current_vendor: dict = Depends(get_current_vendor)
):
    """Upload legal document"""
    vendor_id = current_vendor["id"]
    
    # Validate document type
    valid_types = ["classification_certificate", "saudi_contractors_authority", "municipal_registration"]
    if document_type not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid document type")
    
    # Read file
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > 104857600:  # 100MB
        raise HTTPException(status_code=400, detail="File size exceeds 100MB")
    
    # Generate storage path
    file_ext = os.path.splitext(file.filename)[1]
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    storage_path = f"vendors/{vendor_id}/legal/{document_type}/{unique_filename}"
    
    # Check if document already exists
    existing = supabase.table("vendor_legal_documents")\
        .select("*")\
        .eq("vendor_id", vendor_id)\
        .eq("document_type", document_type)\
        .execute()
    
    # Delete old file from storage if exists
    if existing.data:
        try:
            supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([existing.data[0]["s3_key"]])
        except:
            pass
    
    # Upload to storage
    try:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).upload(
            file=file_content,
            path=storage_path,
            file_options={"cache-control": "3600", "upsert": "false", "content-type": file.content_type}
        )
        file_url = supabase.storage.from_(SUPABASE_STORAGE_BUCKET).get_public_url(storage_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")
    
    # Save metadata
    doc_data = {
        "vendor_id": vendor_id,
        "document_type": document_type,
        "file_name": file.filename,
        "file_size": file_size,
        "file_type": file.content_type,
        "s3_bucket": SUPABASE_STORAGE_BUCKET,
        "s3_key": storage_path,
        "s3_url": file_url
    }
    
    if existing.data:
        # Update existing
        result = supabase.table("vendor_legal_documents")\
            .update(doc_data)\
            .eq("id", existing.data[0]["id"])\
            .execute()
    else:
        # Insert new
        result = supabase.table("vendor_legal_documents")\
            .insert(doc_data)\
            .execute()
    
    return result.data[0]

@router.delete("/legal-document/{document_type}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_legal_document(document_type: str, current_vendor: dict = Depends(get_current_vendor)):
    """Delete legal document"""
    vendor_id = current_vendor["id"]
    
    doc = supabase.table("vendor_legal_documents")\
        .select("*")\
        .eq("vendor_id", vendor_id)\
        .eq("document_type", document_type)\
        .execute()
    
    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from storage
    try:
        supabase.storage.from_(SUPABASE_STORAGE_BUCKET).remove([doc.data[0]["s3_key"]])
    except:
        pass
    
    # Delete from database
    supabase.table("vendor_legal_documents").delete().eq("id", doc.data[0]["id"]).execute()
    return None