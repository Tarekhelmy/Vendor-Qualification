import numpy as np
from PIL import Image
import base64
import io
from typing import List

try:
    import cv2
    CV2_SUPPORT = True
except ImportError:
    CV2_SUPPORT = False
    print("Warning: OpenCV not available. Image preprocessing will be basic.")

try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError as e:
    PDF_SUPPORT = False
    print("Error: PyMuPDF not available. PDF files won't be supported. use pip install PyMuPDF")
    raise e

class FileConverter:
    """Class to extract invoice information using the Anthropic API."""
    def __init__(self):
        """Initialize the ImageProcessing class."""
        pass
    def preprocess_image(self,pil_image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR."""
        if CV2_SUPPORT:
            return self.enhance_image_opencv(pil_image)
        else:
            return self.enhance_image_basic(pil_image)
        
    def pil_to_base64(self,pil_image: Image.Image) -> str:
        """Convert PIL Image to base64 string with compression."""
        # First compress the image to fit API limits
        compressed_image = self.compress_image_for_api(pil_image)
        
        # Convert to base64
        buffer = io.BytesIO()
        compressed_image.save(buffer, format='JPEG', quality=85, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def enhance_image_basic(self,pil_image: Image.Image) -> Image.Image:
        """Basic image enhancement without OpenCV."""
        try:
            # Convert to grayscale and back to RGB for better contrast
            grayscale = pil_image.convert('L')
            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(grayscale.convert('RGB'))
            enhanced = enhancer.enhance(1.5)
            return enhanced
        except:
            return pil_image

    def enhance_image_opencv(self,pil_image: Image.Image) -> Image.Image:
        """Enhanced image preprocessing with OpenCV."""
        try:
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            
            # Apply Gaussian blur to reduce noise
            blurred = cv2.GaussianBlur(opencv_image, (3, 3), 0)
            
            # Convert to grayscale
            gray = cv2.cvtColor(blurred, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Convert back to PIL Image
            return Image.fromarray(thresh).convert('RGB')
        except Exception as e:
            print(f"OpenCV enhancement failed: {e}")
            return self.enhance_image_basic(pil_image)
        
    def compress_image_for_api(self,pil_image: Image.Image, max_size_mb: float = 4.5) -> Image.Image:
        """Compress image to fit within API limits."""
        max_size_bytes = max_size_mb * 1024 * 1024
        
        # Start with original image
        current_image = pil_image.copy()
        quality = 95
        
        while quality > 20:
            # Test current size
            buffer = io.BytesIO()
            current_image.save(buffer, format='JPEG', quality=quality, optimize=True)
            current_size = len(buffer.getvalue())
            
            print(f"Testing compression: quality={quality}, size={current_size/1024/1024:.1f}MB")
            
            if current_size <= max_size_bytes:
                print(f"✅ Image compressed successfully: {current_size/1024/1024:.1f}MB")
                return current_image
            
            # Reduce quality
            quality -= 10
            
            # If still too large at low quality, resize image
            if quality <= 30:
                width, height = current_image.size
                new_width = int(width * 0.8)
                new_height = int(height * 0.8)
                current_image = current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resizing image to {new_width}x{new_height}")
                quality = 80  # Reset quality after resize
        
        # Final fallback - very small image
        print("⚠️ Using aggressive compression")
        width, height = current_image.size
        current_image = current_image.resize((int(width * 0.5), int(height * 0.5)), Image.Resampling.LANCZOS)
        return current_image
    
    def convert_file_to_base64_images(self,file_content: bytes,file_type) -> List[Image.Image]:
        if not file_type == 'pdf':
            raise ValueError("This method only supports PDF files.")
        try:
            pdf_document = fitz.open("pdf", file_content)
            images = []
            
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                
                # Start with lower DPI to avoid huge images
                matrix = fitz.Matrix(100/72, 100/72)  # 200 DPI instead of 300
                pix = page.get_pixmap(matrix=matrix)
                img_data = pix.tobytes("ppm")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Check size and adjust if needed
                width, height = pil_image.size
                if width * height > 4000000:  # If more than 4MP, resize
                    ratio = (3000000 / (width * height)) ** 0.5
                    new_width = int(width * ratio)
                    new_height = int(height * ratio)
                    pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"Resized page {page_num+1} from {width}x{height} to {new_width}x{new_height}")
                
                preprocessed_image = self.preprocess_image(pil_image)
                base64_image = self.pil_to_base64(preprocessed_image)
                images.append(base64_image)
            
            pdf_document.close()
            return images

        except Exception as e:
            print(f"Error converting PDF: {str(e)}")
            return []

    
    def convert_image_to_base64_images(self, image_content: bytes) -> List[Image.Image]:
        """Convert image bytes to PIL Image."""
        try:
            pil_image = Image.open(io.BytesIO(image_content))
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            # Check if image is too large
            width, height = pil_image.size
            if width * height > 4000000:  # If more than 4MP, resize
                ratio = (3000000 / (width * height)) ** 0.5
                new_width = int(width * ratio)
                new_height = int(height * ratio)
                pil_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"Resized image from {width}x{height} to {new_width}x{new_height}")
            preprocessed_image = self.preprocess_image(pil_image)
            base64_image = self.pil_to_base64(preprocessed_image)
            
            return base64_image
        except Exception as e:
            print(f"Error converting image: {str(e)}")
            return None