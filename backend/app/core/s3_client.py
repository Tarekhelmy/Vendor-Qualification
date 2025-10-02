import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class S3Client:
    def __init__(self):
        # Support for custom S3-compatible storage (MinIO, DigitalOcean Spaces, Wasabi, etc.)
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL,  # Custom S3 endpoint
            region_name=settings.S3_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME
        self.use_custom_s3 = settings.S3_ENDPOINT_URL is not None
    
    def upload_file(self, file_content: bytes, file_key: str, content_type: str) -> str:
        """
        Upload file to S3 and return the URL
        
        Args:
            file_content: File content as bytes
            file_key: S3 key (path) for the file
            content_type: MIME type of the file
            
        Returns:
            S3 URL of the uploaded file
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType=content_type
            )
            
            # Generate URL
            url = f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{file_key}"
            return url
            
        except ClientError as e:
            logger.error(f"Error uploading file to S3: {str(e)}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    def delete_file(self, file_key: str) -> bool:
        """
        Delete file from S3
        
        Args:
            file_key: S3 key (path) of the file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
            
        except ClientError as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False
    
    def generate_presigned_url(self, file_key: str, expiration: int = 3600) -> str:
        """
        Generate a presigned URL for temporary access to a file
        
        Args:
            file_key: S3 key (path) of the file
            expiration: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Presigned URL
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': file_key},
                ExpiresIn=expiration
            )
            return url
            
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            raise Exception(f"Failed to generate download URL: {str(e)}")

s3_client = S3Client()