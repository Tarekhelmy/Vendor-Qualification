This document provides a structured overview of the **Vendor Qualification Portal** database schema, which is based on the provided PostgreSQL Data Definition Language (DDL).

The design centers around three core entities: **Vendors**, **Projects**, and the many-to-many relationship tracked by **Vendor Applications**.

---

# 1. Core Structure & Relationships

These tables define the fundamental entities and the central link that represents a vendor's application to a project.

| Table | Description | Primary Key (PK) | Foreign Keys (FK) | Core Relationships |
| :--- | :--- | :--- | :--- | :--- |
| **`vendors`** | Stores vendor company details and links directly to the Supabase authentication system (`auth.users`). | `id` (UUID) | `user_id` (→ `auth.users`) | **1:M** with `vendor_applications`. |
| **`projects`** | Stores pre-defined projects available for qualification. | `id` (UUID) | None | **1:M** with `vendor_applications`. |
| **`vendor_applications`** | The central table tracking a single application by a vendor for a project. | `id` (UUID) | `vendor_id` (→ `vendors`), `project_id` (→ `projects`) | **M:M** junction with a unique constraint on (`vendor_id`, `project_id`). |

---

# 2. Application Tracking & Generic Documents

These tables manage the submission process and handle generic file uploads associated with the application.

| Table | Description | Links To | Key Data Points |
| :--- | :--- | :--- | :--- |
| **`form_submissions`** | Tracks the completion status, lock status, and form data (as JSONB) for each of the 14 forms within an application. | `application_id` (→ `vendor_applications`) | `form_number` (1-14), `is_complete`, `is_locked`, `form_data` (JSONB). |
| **`document_uploads`** | Stores metadata and S3 location for generic files uploaded across various forms (Forms 1-14). | `application_id` (→ `vendor_applications`), `related_entity_id` (Links to specific records like `contractor_completed_projects`). | `form_number`, `document_type`, `s3_key`, `s3_url`. |

---

# 3. Vendor Profile Documents

These tables store documents related to the vendor's company profile, independent of a specific project application.

| Table | Description | Links To | Unique Constraints | Document Types (for `vendor_legal_documents`) |
| :--- | :--- | :--- | :--- | :--- |
| **`vendor_financial_statements`** | Stores vendor financial statement documents. | `vendor_id` (→ `vendors`) | **UNIQUE** on (`vendor_id`, `year`). | N/A |
| **`vendor_legal_documents`** | Stores vendor legal and official documents. | `vendor_id` (→ `vendors`) | **UNIQUE** on (`vendor_id`, `document_type`). | `classification_certificate`, `saudi_contractors_authority`, `municipal_registration`. |

---

# 4. Form Data Tables (Project Experience & Detail)

These tables capture the detailed project history required in Forms 1, 2, and 3.

| Table | Form | Description | Links To | Key Relationships |
| :--- | :--- | :--- | :--- | :--- |
| **`contractor_completed_projects`** | Form 1 | List of projects completed within the last 5 years. | `application_id` (→ `vendor_applications`) | 1:M with `document_uploads` (via `related_entity_id`). |
| **`contractor_ongoing_projects`** | Form 2 | List of the vendor's currently active projects. | `application_id` (→ `vendor_applications`) | **1:1** with `project_profiles` (via `ongoing_project_id`). |
| **`project_profiles`** | Form 3 | Detailed profile information for each **ongoing project** listed in Form 2. | `ongoing_project_id` (→ `contractor_ongoing_projects`) | **1:M** with four child tables: `project_personnel`, `project_equipment`, `project_materials`, and `project_subcontractors`. |

---

# 5. Form Data Tables (Personnel & Resources)

These tables track the vendor's human resources and equipment, used in Forms 4, 5, 6, and 7.

| Table | Form | Description | Links To | Supporting Tables |
| :--- | :--- | :--- | :--- | :--- |
| **`management_personnel`** | Form 4 | Details of the vendor's management and supervisory staff. | `application_id` (→ `vendor_applications`) | `position_templates`, `project_required_positions`, `application_position_assignments` (links `management_personnel` to an `application`). |
| **`personnel_resumes`** | Form 5 | Central table for personnel resume details. | `personnel_id` (→ `management_personnel`) | `personnel_education`, `personnel_work_experience` (Detail tables for the resume). |
| **`contractor_workforce_positions`** | Form 6 | Vendor's total workforce by **position name** (e.g., Electrical Engineer). | `application_id` (→ `vendor_applications`) | `position_templates`, `project_required_positions`. |
| **`skilled_unskilled_manpower`** | Form 6 | Vendor's total workforce by **craft/trade** (e.g., Welder, Helper), often grouped by nationality. | `application_id` (→ `vendor_applications`) | `manpower_craft_templates`, `project_required_crafts`. |
| **`contractor_equipment_tools`** | Form 7 | List of equipment and tools owned by the contractor. | `application_id` (→ `vendor_applications`) | `equipment_tool_templates`, `project_required_equipment`. |

---

# 6. Form Data Tables (Questionnaire)

These tables handle the project-specific questions and the vendor's answers (Form 8).

| Table | Form | Description | Links To | Key Relationships |
| :--- | :--- | :--- | :--- | :--- |
| **`questionnaire_questions`** | Form 8 | Defines the list of questions for a specific project. | `project_id` (→ `projects`) | **1:M** with `questionnaire_responses`. |
| **`questionnaire_responses`** | Form 8 | Stores the vendor's text answer to a specific question. | `application_id` (→ `vendor_applications`), `question_id` (→ `questionnaire_questions`) | **1:M** with `questionnaire_attachments`. |
| **`questionnaire_attachments`** | Form 8 | Stores documents uploaded specifically as evidence for a questionnaire response. | `response_id` (→ `questionnaire_responses`) | N/A |