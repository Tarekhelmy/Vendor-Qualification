# Vendor Qualification Portal

A full-stack web application for vendors to apply for project qualifications. Built with **FastAPI** (backend) and **React** (frontend), using **Supabase** for database and **AWS S3** for document storage.

## 🎯 Features

- **Multi-Application Management**: Vendors can apply to multiple projects simultaneously
- **14 Forms System**: Comprehensive forms for qualification (Form 1 implemented)
- **Auto-Save**: Real-time form data saving with visual feedback
- **Document Management**: Upload and manage documents per form (S3 storage)
- **Status Tracking**: Track application status (Draft → Submitted → Under Review → Reviewed)
- **Form Locking**: Submitted forms are locked, requiring admin permission to unlock
- **Responsive UI**: Modern, mobile-friendly interface with Tailwind CSS

## 📋 Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account
- AWS account with S3 bucket
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd vendor-portal
```

### 2. Database Setup (Supabase)

1. Create a new Supabase project at https://supabase.com
2. Go to SQL Editor and execute the schema from `supabase_schema.sql`
3. Note your `SUPABASE_URL` and `SUPABASE_ANON_KEY` from Project Settings → API

### 3. AWS S3 Setup

1. Create an S3 bucket in your AWS account
2. Create an IAM user with S3 permissions
3. Note your `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and bucket name

### 4. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
```

**Edit `backend/.env`:**
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS