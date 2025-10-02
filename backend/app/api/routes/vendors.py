from fastapi import APIRouter, Depends
from app.schemas.schemas import ProjectResponse
from app.core.security import get_current_vendor
from app.core.database import supabase
from typing import List

router = APIRouter()

@router.get("/projects", response_model=List[ProjectResponse])
async def get_available_projects(current_vendor: dict = Depends(get_current_vendor)):
    """
    Get all active projects available for application
    """
    response = supabase.table("projects")\
        .select("*")\
        .eq("is_active", True)\
        .execute()
    
    return response.data