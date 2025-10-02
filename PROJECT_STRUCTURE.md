# Vendor Qualification Portal - Project Structure

## Backend (FastAPI)

```
backend/
├── app/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── auth.py              # Authentication endpoints
│   │       ├── vendors.py           # Vendor-related endpoints
│   │       ├── applications.py      # Application CRUD endpoints
│   │       ├── forms.py             # Form 1 endpoints (expandable for 14 forms)
│   │       └── documents.py         # Document upload/download endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                # Settings and configuration
│   │   ├── database.py              # Supabase client
│   │   ├── s3_client.py             # AWS S3 client
│   │   └── security.py              # JWT authentication & password hashing
│   └── schemas/
│       ├── __init__.py
│       └── schemas.py               # Pydantic models for validation
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
└── .env                             # Environment variables (create from .env.example)
```

## Frontend (React + Vite)

```
frontend/
├── public/
├── src/
│   ├── api/
│   │   └── client.js                # Axios API client with interceptors
│   ├── stores/
│   │   └── authStore.js             # Zustand auth state management
│   ├── pages/
│   │   ├── Login.jsx                # Login page
│   │   ├── Dashboard.jsx            # Vendor dashboard (portal home)
│   │   ├── ApplicationDetail.jsx    # Application detail with form list
│   │   └── forms/
│   │       └── Form1.jsx            # Form 1: Completed Projects
│   ├── App.jsx                      # Main app with routing
│   ├── main.jsx                     # React entry point
│   └── index.css                    # Tailwind CSS
├── package.json
├── vite.config.js
├── tailwind.config.js
└── .env                             # Frontend environment variables
```

## Database (Supabase)

Execute the SQL schema provided in `supabase_schema.sql` to create all necessary tables.

### Key Tables:
- `vendors` - Vendor accounts
- `projects` - Available projects
- `vendor_applications` - Vendor project applications
- `form_submissions` - Tracks form completion status
- `contractor_completed_projects` - Form 1 data
- `document_uploads` - Document metadata

## File Storage (AWS S3)

Documents are organized in S3 as:
```
s3://your-bucket/
└── applications/
    └── {application_id}/
        └── form_{form_number}/
            └── {document_type}/
                └── {unique_filename}
```

## Key Features Implemented

### Auto-Save Functionality
- Real-time saving on field changes
- Visual feedback (Saving... / Saved)
- Debounced updates to backend

### Form 1 Features
- ✅ Dynamic project rows (add/remove)
- ✅ All required fields with validation
- ✅ Document upload per project (contract, invoices)
- ✅ Form submission with locking
- ✅ Auto-save on field changes
- ✅ S3 document storage
- ✅ View/delete uploaded documents

### Application Management
- ✅ Create applications for available projects
- ✅ Track application status
- ✅ Navigate between forms
- ✅ Lock forms after submission

### Authentication
- ✅ JWT-based authentication
- ✅ Protected routes
- ✅ Token refresh handling
- ✅ Vendor-specific data access