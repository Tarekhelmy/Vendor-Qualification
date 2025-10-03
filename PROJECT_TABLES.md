# Vendor Qualification Portal - Database Schema Documentation

## Overview
This document describes the database structure for a vendor qualification portal system built with Supabase (PostgreSQL). The system manages vendor applications for project qualifications through an 8-form submission process.

---

## Core Tables

### `vendors`
Stores vendor company information and links to Supabase Auth users.

**Columns:**
- `id` (UUID, PK): Unique vendor identifier
- `user_id` (UUID, FK → auth.users): Links to Supabase authentication
- `company_name` (VARCHAR): Company legal name
- `contact_person_name` (VARCHAR): Primary contact name
- `contact_person_email` (VARCHAR, UNIQUE): Contact email
- `contact_person_phone` (VARCHAR): Contact phone number
- `is_active` (BOOLEAN): Account status flag
- `created_at`, `updated_at` (TIMESTAMP): Audit timestamps

**Used By:** All forms reference this table to identify the vendor submitting data.

---

### `projects`
Pre-defined projects that vendors can apply to.

**Columns:**
- `id` (UUID, PK): Unique project identifier
- `project_name` (VARCHAR): Display name
- `project_code` (VARCHAR, UNIQUE): Internal reference code
- `description` (TEXT): Project details
- `is_active` (BOOLEAN): Whether project accepts applications
- `created_at`, `updated_at` (TIMESTAMP): Audit timestamps

**Used By:** Application creation, form requirements (required positions, equipment, crafts, questionnaire questions).

---

### `vendor_applications`
Tracks vendor applications to specific projects. One application per vendor per project.

**Columns:**
- `id` (UUID, PK): Unique application identifier
- `vendor_id` (UUID, FK → vendors): Applicant vendor
- `project_id` (UUID, FK → projects): Target project
- `status` (VARCHAR): Application status (draft, submitted, under_review, reviewed)
- `submitted_at` (TIMESTAMP): When application was submitted
- `created_at`, `updated_at` (TIMESTAMP): Audit timestamps
- **UNIQUE CONSTRAINT:** (vendor_id, project_id)

**Used By:** All 8 forms link to this table to associate data with a specific application.

---

### `form_submissions`
Tracks completion status of each of the 8 forms per application.

**Columns:**
- `id` (UUID, PK): Unique submission identifier
- `application_id` (UUID, FK → vendor_applications): Associated application
- `form_number` (INTEGER): Form identifier (1-8)
- `form_data` (JSONB): Optional unstructured data storage
- `is_locked` (BOOLEAN): Whether form is editable
- `is_complete` (BOOLEAN): Whether form is finished
- `last_saved_at` (TIMESTAMP): Last auto-save timestamp
- `submitted_at` (TIMESTAMP): When form was submitted
- `created_at`, `updated_at` (TIMESTAMP): Audit timestamps
- **UNIQUE CONSTRAINT:** (application_id, form_number)

**Used By:** Every form checks this table to determine if it's locked or complete.

---

## Form 1: Completed Projects

### `contractor_completed_projects`
Projects completed within the last 5 years.

**Columns:**
- `id` (UUID, PK)
- `vendor_id`, `application_id` (FK)
- `project_field` (VARCHAR): Similar/Related/Other
- `contract_number`, `contract_signing_date` (VARCHAR, DATE)
- `client_name`, `client_representative_name`, `client_phone` (VARCHAR)
- `project_title`, `project_description` (TEXT)
- `contract_start_date`, `contract_completion_date` (DATE)
- `contract_value_sar` (DECIMAL): Project value in Saudi Riyals
- `created_at`, `updated_at` (TIMESTAMP)

**Documents Required:** Contracts, Invoices (linked via `document_uploads`)

---

## Form 2: Ongoing Projects

### `contractor_ongoing_projects`
Currently active projects.

**Columns:**
- `id` (UUID, PK)
- `vendor_id`, `application_id` (FK)
- `project_field` (VARCHAR): Similar/Related/Other
- `contract_number`, `contract_signing_date` (VARCHAR, DATE)
- `client_name` (VARCHAR)
- `project_title`, `project_description` (TEXT)
- `contract_start_date`, `contract_completion_date` (DATE)
- `contract_value_sar` (DECIMAL)
- `percent_completion` (DECIMAL): 0-100
- `completed_value_sar` (DECIMAL): Auto-calculated completion value
- `created_at`, `updated_at` (TIMESTAMP)

**Documents Required:** Contracts

---

## Form 3: Project Profiles

### `project_profiles`
Detailed profiles for each ongoing project from Form 2.

**Columns:**
- `id` (UUID, PK)
- `vendor_id`, `application_id` (FK)
- `ongoing_project_id` (UUID, FK → contractor_ongoing_projects, UNIQUE)
- `contract_number`, `contract_signed_date`, `contract_title` (VARCHAR, DATE, TEXT)
- `completion_date`, `forecasted_completion_date` (DATE)
- `client_name` (VARCHAR)
- `percent_completion` (DECIMAL)
- `representative_name`, `representative_position`, `representative_phone` (VARCHAR)
- `management_count`, `supervisory_count`, `skilled_count`, `unskilled_count` (INTEGER)
- `contract_type` (VARCHAR)
- `contract_value_sar` (DECIMAL)
- `contractor_role` (VARCHAR): Main Contractor/Subcontractor
- `created_at`, `updated_at` (TIMESTAMP)

**Related Tables:**
- `project_personnel`: Staff assigned (position, name)
- `project_equipment`: Equipment used (equipment_name)
- `project_materials`: Materials used (material_name)
- `project_subcontractors`: Subcontractors (name, description, value)

---

## Form 4: Management & Supervisory Personnel

### `management_personnel`
Total management and supervisory staff.

**Columns:**
- `id` (UUID, PK)
- `vendor_id`, `application_id` (FK)
- `full_name`, `position` (VARCHAR)
- `nationality` (VARCHAR)
- `highest_educational_qualification` (VARCHAR)
- `experience_with_company`, `experience_on_sec_erb_projects`, `experience_total` (INTEGER): Years
- `created_at`, `updated_at` (TIMESTAMP)

**Related Tables:**
- `position_templates`: Pre-defined positions (Project Manager, Engineer, etc.)
- `project_required_positions`: Required positions per project with minimum counts

---

## Form 5: Personnel Resumes

### `personnel_resumes`
Detailed resumes for personnel from Form 4.

**Columns:**
- `id` (UUID, PK)
- `personnel_id` (UUID, FK → management_personnel, UNIQUE)
- `application_id` (FK)
- `date_of_birth` (DATE)
- `additional_notes` (TEXT)
- `created_at`, `updated_at` (TIMESTAMP)

**Related Tables:**
- `personnel_education`: Education history (institution, years, qualifications, degrees)
- `personnel_work_experience`: Work history (company, position, dates, job description, is_current)

---

## Form 6: Skilled & Unskilled Manpower

### `skilled_unskilled_manpower`
Breakdown of all workforce by craft/position.

**Columns:**
- `id` (UUID, PK)
- `vendor_id`, `application_id` (FK)
- `craft_name` (VARCHAR): Job title/role
- `nationality` (VARCHAR): Can include multiple (e.g., "Egyptian, Indian")
- `quantity` (INTEGER): Number of workers
- `created_at`, `updated_at` (TIMESTAMP)

**Related Tables:**
- `manpower_craft_templates`: 30+ pre-defined crafts
- `project_required_crafts`: Required crafts per project with minimum quantities

---

## Form 7: Equipment & Tools

### `contractor_equipment_tools`
Inventory of equipment and machinery.

**Columns:**
- `id` (UUID, PK)
- `vendor_id`, `application_id` (FK)
- `equipment_type` (VARCHAR): Equipment name
- `capacity` (VARCHAR): Specifications
- `year_of_manufacture` (VARCHAR): Year or range (e.g., "2018-2022")
- `quantity` (INTEGER)
- `present_location` (VARCHAR): Where equipment is stored
- `created_at`, `updated_at` (TIMESTAMP)

**Related Tables:**
- `equipment_tool_templates`: 35+ pre-defined equipment types
- `project_required_equipment`: Required equipment per project with minimum quantities

---

## Form 8: Questionnaire

### `questionnaire_questions`
Project-specific questions (configurable per project).

**Columns:**
- `id` (UUID, PK)
- `project_id` (UUID, FK → projects, nullable)
- `question_number` (INTEGER)
- `question_text` (TEXT)
- `requires_attachment` (BOOLEAN): Whether attachments are allowed
- `is_active` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)
- **UNIQUE CONSTRAINT:** (project_id, question_number)

### `questionnaire_responses`
Vendor answers to questions.

**Columns:**
- `id` (UUID, PK)
- `vendor_id`, `application_id` (FK)
- `question_id` (UUID, FK → questionnaire_questions)
- `answer_text` (TEXT)
- `created_at`, `updated_at` (TIMESTAMP)
- **UNIQUE CONSTRAINT:** (application_id, question_id)

### `questionnaire_attachments`
Files uploaded with answers (optional).

**Columns:**
- `id` (UUID, PK)
- `response_id` (UUID, FK → questionnaire_responses)
- `document_type`, `file_name`, `file_size`, `file_type` (VARCHAR, BIGINT, VARCHAR)
- `s3_bucket`, `s3_key`, `s3_url` (VARCHAR, TEXT, TEXT)
- `uploaded_at` (TIMESTAMP)

---

## Vendor Profile Documents

### `vendor_financial_statements`
Financial statements for last 5 years (profile page).

**Columns:**
- `id` (UUID, PK)
- `vendor_id` (UUID, FK → vendors)
- `year` (INTEGER): Financial year
- `file_name`, `file_size`, `file_type` (VARCHAR, BIGINT, VARCHAR)
- `s3_bucket`, `s3_key`, `s3_url` (VARCHAR, TEXT, TEXT)
- `uploaded_at` (TIMESTAMP)
- **UNIQUE CONSTRAINT:** (vendor_id, year)

### `vendor_legal_documents`
Required legal certificates (profile page).

**Columns:**
- `id` (UUID, PK)
- `vendor_id` (UUID, FK → vendors)
- `document_type` (VARCHAR): classification_certificate, saudi_contractors_authority, municipal_registration
- `file_name`, `file_size`, `file_type` (VARCHAR, BIGINT, VARCHAR)
- `s3_bucket`, `s3_key`, `s3_url` (VARCHAR, TEXT, TEXT)
- `uploaded_at` (TIMESTAMP)
- **UNIQUE CONSTRAINT:** (vendor_id, document_type)

---

## Document Storage

### `document_uploads`
Generic document storage for all forms (Forms 1-3 use this).

**Columns:**
- `id` (UUID, PK)
- `application_id` (UUID, FK → vendor_applications)
- `form_number` (INTEGER): Which form (1-14)
- `related_entity_id` (UUID): Links to specific record (e.g., project ID)
- `document_type` (VARCHAR): contract, invoice, etc.
- `file_name`, `file_size`, `file_type` (VARCHAR, BIGINT, VARCHAR)
- `s3_bucket`, `s3_key`, `s3_url` (VARCHAR, TEXT, TEXT)
- `uploaded_at`, `created_at` (TIMESTAMP)

---

## Data Flow Summary

1. **Vendor Registration**: Admin creates vendor account → `vendors` table
2. **Application Creation**: Vendor applies to project → `vendor_applications` table
3. **Form Completion**: Vendor fills 8 forms → Data goes to respective tables + `form_submissions` tracks status
4. **Document Upload**: Files stored in Supabase Storage, metadata in various document tables
5. **Profile Management**: Financial/legal docs uploaded to profile → `vendor_financial_statements` + `vendor_legal_documents`
6. **Submission**: Forms locked when submitted, application status updated

All tables use UUID primary keys and include audit timestamps (created_at, updated_at with automatic triggers).