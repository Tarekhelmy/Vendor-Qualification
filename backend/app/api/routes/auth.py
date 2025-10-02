from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.schemas import VendorLogin, Token, VendorResponse
from app.core.security import get_current_vendor
from app.core.database import supabase
from typing import Optional
import os
from dotenv import load_dotenv
from supabase import create_client, Client

router = APIRouter()

load_dotenv()

supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

@router.post("/login", response_model=Token)
async def login(credentials: VendorLogin):
    """
    Vendor login endpoint using Supabase Auth
    Returns Supabase Auth token for authenticated sessions
    """
    try:
        # Sign in with Supabase Auth
        response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password
        })
        
        # Check if we got a session
        if not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Verify vendor exists and is active
        vendor_response = supabase.table("vendors")\
            .select("*")\
            .eq("user_id", response.user.id)\
            .eq("is_active", True)\
            .execute()
        
        if not vendor_response.data or len(vendor_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Vendor account not found or inactive"
            )
        
        return {
            "access_token": response.session.access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")  # Debug
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

@router.get("/me", response_model=VendorResponse)
async def get_current_vendor_info(current_vendor: dict = Depends(get_current_vendor)):
    """
    Get current authenticated vendor information
    """
    return current_vendor

@router.post("/logout")
async def logout(current_vendor: dict = Depends(get_current_vendor)):
    """
    Logout endpoint
    Note: Token invalidation happens on client side
    For server-side logout, implement token blacklisting if needed
    """
    return {"message": "Successfully logged out"}