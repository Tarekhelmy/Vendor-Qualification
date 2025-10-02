from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

def create_vendor(email, password, company_name, contact_name, phone):
    """Create vendor with Supabase Auth"""
    
    # Step 1: Create auth user
    try:
        auth_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            print("❌ Failed to create auth user")
            return
        
        user_id = auth_response.user.id
        print(f"✅ Created auth user: {user_id}")
        
        # Step 2: Create vendor record
        vendor_data = {
            "user_id": user_id,
            "company_name": company_name,
            "contact_person_name": contact_name,
            "contact_person_email": email,
            "contact_person_phone": phone,
            "is_active": True
        }
        
        vendor_response = supabase.table("vendors").insert(vendor_data).execute()
        
        print("✅ Created vendor record!")
        print(f"📧 Email: {email}")
        print(f"🔑 Password: {password}")
        print(f"🏢 Company: {company_name}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Example usage
if __name__ == "__main__":
    create_vendor(
        email="tarekuni@hotmail.com",
        password="password123",
        company_name="Test Company Ltd",
        contact_name="John Doe",
        phone="+966501234567"
    )