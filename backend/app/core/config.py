from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    
    # S3 Storage (Custom S3-compatible or AWS S3)
    S3_ACCESS_KEY_ID: str
    S3_SECRET_ACCESS_KEY: str
    S3_REGION: str = "us-east-1"
    S3_BUCKET_NAME: str
    S3_ENDPOINT_URL: Optional[str] = None
    
    # File Upload
    MAX_FILE_SIZE: int = 104857600  # 100MB
    ALLOWED_FILE_TYPES: str = ".pdf,.doc,.docx,.jpg,.jpeg,.png"
    
    # Environment
    ENVIRONMENT: str = "development"
    
    @property
    def allowed_extensions(self):
        """Get allowed file extensions as a list"""
        return [ext.strip() for ext in self.ALLOWED_FILE_TYPES.split(',')]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# If SUPABASE_KEY is not set but SUPABASE_ANON_KEY is, use that
if not os.getenv('SUPABASE_KEY') and os.getenv('SUPABASE_ANON_KEY'):
    os.environ['SUPABASE_KEY'] = os.getenv('SUPABASE_ANON_KEY')

settings = Settings()