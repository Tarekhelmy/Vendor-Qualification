from supabase import create_client, Client
from app.core.config import settings

def get_supabase_client() -> Client:
    """Get Supabase client instance"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

supabase: Client = get_supabase_client()