from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.database import supabase

security = HTTPBearer()

async def get_current_vendor(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Get current authenticated vendor from Supabase Auth token
    """
    try:
        # Get token from Authorization header
        token = credentials.credentials
        
        # Set the auth token for this request
        supabase.auth.set_session(token, token)
        
        # Get user from token
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        
        user_id = user.user.id
        
        # Get vendor details from vendors table using user_id
        vendor_response = supabase.table("vendors")\
            .select("*")\
            .eq("user_id", user_id)\
            .eq("is_active", True)\
            .execute()
        
        if not vendor_response.data or len(vendor_response.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor account not found"
            )
        
        return dict(vendor_response.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Auth error: {type(e).__name__}: {str(e)}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )