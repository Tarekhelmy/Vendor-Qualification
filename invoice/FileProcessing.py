import requests
from typing import Optional
from invoice.FileConversion import FileConverter
from PIL import Image
import io


class FileProcessor:
    """Class to extract invoice information using the Anthropic API."""
    def __init__(self):
        """Initialize the ImageProcessing class."""
        self.file_converter = FileConverter()
        pass
    
    def download_file_from_uri(self,file_uri: str) -> Optional[bytes]:
        """Download file from public URI."""
        try:
            print(f"Downloading file from: {file_uri}")
            response = requests.get(file_uri, timeout=30)
            response.raise_for_status()
            print(f"Successfully downloaded file ({len(response.content)} bytes)")
            return response.content
        except Exception as e:
            print(f"Error downloading file: {str(e)}")
            return None

    def detect_file_type(self,file_content: bytes) -> str:
        """Detect file type from content bytes."""
        if file_content.startswith(b'%PDF'):
            return 'pdf'
        
        image_signatures = [
            (b'\xff\xd8\xff', 'jpeg'),
            (b'\x89PNG\r\n\x1a\n', 'png'),
            (b'GIF87a', 'gif'),
            (b'GIF89a', 'gif'),
            (b'BM', 'bmp'),
        ]
        
        for signature, _ in image_signatures:
            if file_content.startswith(signature):
                return 'image'
        
        if file_content.startswith(b'RIFF') and b'WEBP' in file_content[:12]:
            return 'image'
        
        return 'unknown'

    
    def process_file_from_uri(self,file_uri):
        file_content = self.download_file_from_uri(file_uri)
        file_type = self.detect_file_type(file_content)
        if file_type == 'pdf':
            images = self.file_converter.convert_file_to_base64_images(file_content,file_type='pdf')
            if not images:
                print("No valid images extracted from PDF.")
                return file_type, None
        return images

