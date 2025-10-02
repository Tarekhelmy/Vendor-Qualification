# Quick Reference Guide

## 🚀 Quick Start Commands

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Create vendor account
cd backend
python scripts/create_vendor.py
```

## 🔑 Environment Variables

### Backend (.env)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your_anon_key
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket
SECRET_KEY=openssl_rand_hex_32
```

### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api
```

## 📍 Important URLs

- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:5173
- Supabase Dashboard: https://app.supabase.com

## 🗄️ Database Quick Commands

```sql
-- Create test vendor (password: password123)
INSERT INTO vendors (company_name, contact_person_name, contact_person_email, contact_person_phone, password_hash)
VALUES ('Test Co', 'John Doe', 'test@test.com', '+966501234567', 
'$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7C8qhPMJ2u');

-- Create test project
INSERT INTO projects (project_name, project_code, description, is_active)
VALUES ('Test Project', 'TEST-001', 'Test project description', true);

-- View all applications
SELECT va.*, v.company_name, p.project_name 
FROM vendor_applications va
JOIN vendors v ON va.vendor_id = v.id
JOIN projects p ON va.project_id = p.id;

-- View Form 1 data
SELECT * FROM contractor_completed_projects WHERE application_id = 'xxx';

-- View documents
SELECT * FROM document_uploads WHERE application_id = 'xxx';
```

## 🔧 Common API Endpoints

```bash
# Login
POST /api/auth/login
{"email": "test@test.com", "password": "password123"}

# Get current vendor
GET /api/auth/me
Headers: Authorization: Bearer {token}

# Create application
POST /api/applications
{"project_id": "uuid"}

# Get Form 1 data
GET /api/forms/1/{application_id}

# Add project to Form 1
POST /api/forms/1/{application_id}/projects
{body with project data}

# Upload document
POST /api/documents/upload
FormData: application_id, form_number, document_type, related_entity_id, file
```

## 📁 Project Structure

```
vendor-portal/
├── backend/
│   ├── app/
│   │   ├── api/routes/
│   │   ├── core/
│   │   └── schemas/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── pages/
│   │   ├── stores/
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## 🐛 Common Issues & Fixes

### Issue: CORS Error
```python
# Fix in backend/main.py
allow_origins=["http://localhost:5173"]
```

### Issue: 401 Unauthorized
```javascript
// Clear token and login again
localStorage.removeItem('access_token');
```

### Issue: S3 Upload Fails
```bash
# Check AWS credentials
aws s3 ls s3://your-bucket --profile default
```

### Issue: Database Connection Error
```bash
# Verify in Supabase dashboard
# Check if SUPABASE_URL and SUPABASE_KEY are correct
```

## 🔐 Generate New Secret Key

```bash
openssl rand -hex 32
```

## 📊 Check Application Status

```bash
# Using curl
curl -X GET "http://localhost:8000/api/applications" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Using Python
import requests
headers = {"Authorization": "Bearer YOUR_TOKEN"}
response = requests.get("http://localhost:8000/api/applications", headers=headers)
print(response.json())
```

## 🎨 Tailwind CSS Classes Used

```css
/* Buttons */
bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md

/* Cards */
bg-white shadow rounded-lg p-6

/* Inputs */
border-gray-300 rounded-md focus:border-blue-500 focus:ring-blue-500

/* Status Badges */
px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800
```

## 📝 Form 1 Field Types

| Field | Type | Required |
|-------|------|----------|
| project_field | Select (Similar/Related/Other) | ✅ |
| contract_number | Text | ❌ |
| contract_signing_date | Date | ❌ |
| client_name | Text | ✅ |
| client_representative_name | Text | ❌ |
| client_phone | Tel | ❌ |
| project_title | Text | ✅ |
| project_description | Textarea | ❌ |
| contract_start_date | Date | ✅ |
| contract_completion_date | Date | ✅ |
| contract_value_sar | Number | ❌ |

## 🔄 Adding New Form Checklist

- [ ] Define data model
- [ ] Create database table
- [ ] Add to `schemas.py`
- [ ] Create API endpoints in `forms.py`
- [ ] Create React component
- [ ] Add route to `App.jsx`
- [ ] Enable in `ApplicationDetail.jsx`
- [ ] Test CRUD operations
- [ ] Test auto-save
- [ ] Test document upload
- [ ] Test form submission

## 🧪 Test Credentials

```
Email: test@test.com
Password: password123
(Create using create_vendor.py script)
```

## 📦 Deployment Quick Commands

```bash
# Backend (Railway/Render)
git push origin main

# Frontend (Vercel)
npm run build
vercel deploy

# Docker
docker-compose up -d
```

## 💾 Backup Commands

```bash
# Backup Supabase (use Supabase dashboard or CLI)
supabase db dump -f backup.sql

# Backup S3
aws s3 sync s3://your-bucket ./s3-backup
```

## 🔍 Debug Mode

```python
# Backend - Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

```javascript
// Frontend - React DevTools
// Install React DevTools browser extension
```

## 📈 Performance Monitoring

```python
# Add to FastAPI
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

## 🎯 Quick Testing

```bash
# Test API endpoint
curl -X GET http://localhost:8000/health

# Test with authentication
TOKEN="your_jwt_token"
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

---

**Keep this file handy for quick reference during development!**