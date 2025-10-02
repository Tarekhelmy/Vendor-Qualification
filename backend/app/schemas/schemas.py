from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List, Union
from datetime import date, datetime
from decimal import Decimal

# Base configuration for all models - allow extra fields
class BaseConfig:
    model_config = ConfigDict(extra='allow', from_attributes=True)

# Authentication Schemas
class VendorLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class VendorResponse(BaseModel):
    model_config = ConfigDict(extra='ignore', from_attributes=True)
    
    id: str
    company_name: str
    contact_person_name: str
    contact_person_email: str
    contact_person_phone: str
    is_active: bool
    created_at: datetime

# Project Schemas
class ProjectResponse(BaseModel):
    model_config = ConfigDict(extra='ignore', from_attributes=True)
    
    id: str
    project_name: str
    project_code: str
    description: Optional[str]
    is_active: bool

# Application Schemas
class ApplicationCreate(BaseModel):
    project_id: str

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(extra='ignore', from_attributes=True)
    
    id: str
    vendor_id: str
    project_id: str
    status: str
    submitted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    project: Optional[ProjectResponse] = None

# Form 1: Completed Projects Schema
class CompletedProjectCreate(BaseModel):
    project_field: str = Field(..., pattern="^(Similar|Related|Other)$")
    contract_number: Optional[str] = None
    contract_signing_date: Optional[Union[date, str]] = None
    client_name: str = ""  # Allow empty, will be filled later
    client_representative_name: Optional[str] = None
    client_phone: Optional[str] = None
    project_title: str = ""  # Allow empty, will be filled later
    project_description: Optional[str] = None
    contract_start_date: Optional[Union[date, str]] = None  # Made optional
    contract_completion_date: Optional[Union[date, str]] = None  # Made optional
    contract_value_sar: Optional[Union[Decimal, float, str]] = None
    
    @field_validator('contract_number', 'client_representative_name', 'client_phone', 'project_description', 'client_name', 'project_title', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty strings to None for optional fields, keep empty for required"""
        if v == '':
            return ''  # Keep empty strings for now
        return v
    
    @field_validator('contract_signing_date', 'contract_start_date', 'contract_completion_date', mode='before')
    @classmethod
    def validate_dates(cls, v):
        """Handle date validation"""
        if v == '' or v is None:
            return None
        if isinstance(v, str):
            return v
        return v
    
    @field_validator('contract_value_sar', mode='before')
    @classmethod
    def validate_amount(cls, v):
        """Handle decimal/float conversion"""
        if v == '' or v is None:
            return None
        return v

class CompletedProjectUpdate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    project_field: Optional[str] = Field(None, pattern="^(Similar|Related|Other)$")
    contract_number: Optional[str] = None
    contract_signing_date: Optional[Union[date, str]] = None
    client_name: Optional[str] = None
    client_representative_name: Optional[str] = None
    client_phone: Optional[str] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    contract_start_date: Optional[Union[date, str]] = None
    contract_completion_date: Optional[Union[date, str]] = None
    contract_value_sar: Optional[Union[Decimal, float, str]] = None
    
    @field_validator('*', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty strings to None"""
        if v == '':
            return None
        return v

class CompletedProjectResponse(BaseModel):
    model_config = ConfigDict(extra='ignore', from_attributes=True)
    
    id: str
    vendor_id: str
    application_id: str
    project_field: str
    contract_number: Optional[str]
    contract_signing_date: Optional[date]
    client_name: str
    client_representative_name: Optional[str]
    client_phone: Optional[str]
    project_title: str
    project_description: Optional[str]
    contract_start_date: Optional[date]  # Made optional
    contract_completion_date: Optional[date]  # Made optional
    contract_value_sar: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    documents: Optional[List['DocumentResponse']] = []

# Document Schemas
class DocumentResponse(BaseModel):
    model_config = ConfigDict(extra='ignore', from_attributes=True)
    
    id: str
    application_id: str
    form_number: int
    related_entity_id: Optional[str]
    document_type: str
    file_name: str
    file_size: int
    file_type: str
    s3_url: str
    uploaded_at: datetime

# Form Submission Schemas
class FormSubmissionResponse(BaseModel):
    model_config = ConfigDict(extra='ignore', from_attributes=True)
    
    id: str
    application_id: str
    form_number: int
    is_locked: bool
    is_complete: bool
    last_saved_at: datetime
    submitted_at: Optional[datetime]

class FormSubmitRequest(BaseModel):
    form_number: int = Field(..., ge=1, le=14)

# Bulk save for Form 1
class Form1BulkSave(BaseModel):
    application_id: str
    projects: List[CompletedProjectCreate]

class Form1Response(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    projects: List[CompletedProjectResponse]
    form_submission: FormSubmissionResponse

# Form 2: Ongoing Projects
class OngoingProjectCreate(BaseModel):
    project_field: str = Field(..., pattern="^(Similar|Related|Other)$")
    contract_number: Optional[str] = None
    contract_signing_date: Optional[date] = None
    client_name: str
    project_title: str
    project_description: Optional[str] = None
    contract_start_date: Optional[date] = None  # Changed from required to Optional
    contract_completion_date: Optional[date] = None  # Changed from required to Optional
    contract_value_sar: Optional[Decimal] = None
    percent_completion: Optional[Decimal] = Field(None, ge=0, le=100)
    completed_value_sar: Optional[Decimal] = None

class OngoingProjectUpdate(BaseModel):
    project_field: Optional[str] = Field(None, pattern="^(Similar|Related|Other)$")
    contract_number: Optional[str] = None
    contract_signing_date: Optional[date] = None
    client_name: Optional[str] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    contract_start_date: Optional[date] = None
    contract_completion_date: Optional[date] = None
    contract_value_sar: Optional[Decimal] = None
    percent_completion: Optional[Decimal] = Field(None, ge=0, le=100)
    completed_value_sar: Optional[Decimal] = None

class OngoingProjectResponse(BaseModel):
    id: str
    vendor_id: str
    application_id: str
    project_field: str
    contract_number: Optional[str]
    contract_signing_date: Optional[date]
    client_name: str
    project_title: str
    project_description: Optional[str]
    contract_start_date: Optional[date]  # Changed to Optional
    contract_completion_date: Optional[date]  # Changed to Optional
    contract_value_sar: Optional[Decimal]
    percent_completion: Optional[Decimal]
    completed_value_sar: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    documents: List[DocumentResponse] = []

class Form2Response(BaseModel):
    projects: List[OngoingProjectResponse]
    form_submission: FormSubmissionResponse

# Form 3: Project Profiles
class PersonnelItem(BaseModel):
    position: str
    name: str

class EquipmentItem(BaseModel):
    equipment_name: str

class MaterialItem(BaseModel):
    material_name: str

class SubcontractorItem(BaseModel):
    contractor_name: str
    work_description: Optional[str] = None
    value_sar: Optional[Decimal] = None

class ProjectProfileCreate(BaseModel):
    ongoing_project_id: str
    contract_number: Optional[str] = None
    contract_signed_date: Optional[date] = None
    contract_title: Optional[str] = None
    completion_date: Optional[date] = None
    forecasted_completion_date: Optional[date] = None
    client_name: Optional[str] = None
    percent_completion: Optional[Decimal] = Field(None, ge=0, le=100)
    representative_name: Optional[str] = None
    representative_position: Optional[str] = None
    representative_phone: Optional[str] = None
    management_count: Optional[int] = Field(0, ge=0)
    supervisory_count: Optional[int] = Field(0, ge=0)
    skilled_count: Optional[int] = Field(0, ge=0)
    unskilled_count: Optional[int] = Field(0, ge=0)
    contract_type: Optional[str] = None
    contract_value_sar: Optional[Decimal] = None
    contractor_role: Optional[str] = Field(None, pattern="^(Main Contractor|Subcontractor)$")

class ProjectProfileUpdate(BaseModel):
    contract_number: Optional[str] = None
    contract_signed_date: Optional[date] = None
    contract_title: Optional[str] = None
    completion_date: Optional[date] = None
    forecasted_completion_date: Optional[date] = None
    client_name: Optional[str] = None
    percent_completion: Optional[Decimal] = Field(None, ge=0, le=100)
    representative_name: Optional[str] = None
    representative_position: Optional[str] = None
    representative_phone: Optional[str] = None
    management_count: Optional[int] = Field(None, ge=0)
    supervisory_count: Optional[int] = Field(None, ge=0)
    skilled_count: Optional[int] = Field(None, ge=0)
    unskilled_count: Optional[int] = Field(None, ge=0)
    contract_type: Optional[str] = None
    contract_value_sar: Optional[Decimal] = None
    contractor_role: Optional[str] = Field(None, pattern="^(Main Contractor|Subcontractor)$")

class PersonnelResponse(BaseModel):
    id: str
    position: str
    name: str

class EquipmentResponse(BaseModel):
    id: str
    equipment_name: str

class MaterialResponse(BaseModel):
    id: str
    material_name: str

class SubcontractorResponse(BaseModel):
    id: str
    contractor_name: str
    work_description: Optional[str]
    value_sar: Optional[Decimal]

class ProjectProfileResponse(BaseModel):
    id: str
    vendor_id: str
    application_id: str
    ongoing_project_id: str
    contract_number: Optional[str]
    contract_signed_date: Optional[date]
    contract_title: Optional[str]
    completion_date: Optional[date]
    forecasted_completion_date: Optional[date]
    client_name: Optional[str]
    percent_completion: Optional[Decimal]
    representative_name: Optional[str]
    representative_position: Optional[str]
    representative_phone: Optional[str]
    management_count: int
    supervisory_count: int
    skilled_count: int
    unskilled_count: int
    contract_type: Optional[str]
    contract_value_sar: Optional[Decimal]
    contractor_role: Optional[str]
    created_at: datetime
    updated_at: datetime
    personnel: List[PersonnelResponse] = []
    equipment: List[EquipmentResponse] = []
    materials: List[MaterialResponse] = []
    subcontractors: List[SubcontractorResponse] = []

class OngoingProjectWithProfile(BaseModel):
    id: str
    project_field: str
    contract_number: Optional[str]
    client_name: str
    project_title: str
    contract_value_sar: Optional[Decimal]
    percent_completion: Optional[Decimal]
    has_profile: bool
    profile_id: Optional[str] = None

class Form3Response(BaseModel):
    ongoing_projects: List[OngoingProjectWithProfile]
    profiles: List[ProjectProfileResponse]
    form_submission: FormSubmissionResponse