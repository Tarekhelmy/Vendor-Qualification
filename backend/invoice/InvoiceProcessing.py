from .InvoiceValidation import InvoiceValidator
from typing import List, Dict
from invoice.Anthropic import LLMInvoiceExtractor # Import the Anthropic client from your tools module
from anthropic import Anthropic
from dotenv import load_dotenv
import os
from datetime import datetime
load_dotenv()
import fitz
import base64
import httpx
import requests

class InvoiceProcessor:
    """Class to extract invoice information using the Anthropic API."""
    def __init__(self):
        """Initialize the ImageProcessing class."""
        self.invoice_validator = InvoiceValidator()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        anthropic = Anthropic(api_key=api_key)
        self.invoice_extractor = LLMInvoiceExtractor(anthropic_client=anthropic)
        pass

    def process_invoice_base64_images(self, base64_images: str) -> List[Dict]:
        """Process invoice."""
        print(f"\n{'='*60}")
        print(f"Processing invoice")
        print(f"{'='*60}")
        
        if not base64_images:
            print("Failed to convert file to images")
            return []
        
        results = []
        # Process each page
        for i, base64_image in enumerate(base64_images):
            print(f"\nProcessing page {i+1}/{len(base64_images)}")
            
            try:
                invoice_data = self.invoice_extractor.extract_invoice_info_simple(base64_image)
                
                if invoice_data:
                    validation = self.invoice_validator.validate_zatca_compliance(invoice_data)
                    
                    invoice_data['page_number'] = i + 1
                    invoice_data['processed_at'] = datetime.now().isoformat()
                    invoice_data['zatca_validation'] = validation
                    
                    results.append(invoice_data)
                    print(f"✅ Successfully processed page {i+1}")
                else:
                    print(f"❌ Failed to process page {i+1}")
                    
            except Exception as e:
                print(f"Error processing page {i+1}: {str(e)}")
        
        # Filter results to only show complete invoices
        complete_results = self.invoice_validator.filter_complete_results(results)
        
        return complete_results
    
    

    def process_invoice_uri(self, uri: str) -> List[Dict]:
        """Process invoice."""
        print(f"\n{'='*60}")
        print(f"Processing invoice")
        print(f"{'='*60}")
        if not uri:
            print("No URI provided")
            return []

        try:
            invoice_data = self.invoice_extractor.extract_invoice_info_uri(uri)
            
            if invoice_data:
                print(invoice_data)
                print(invoice_data['total_amount_including_vat'])
                validation = self.invoice_validator.validate_zatca_compliance(invoice_data)
                
                invoice_data['processed_at'] = datetime.now().isoformat()
                invoice_data['zatca_validation'] = validation
                
                return self.invoice_validator.filter_complete_results(invoice_data)
            else:
                return []
                
        except Exception as e:
            print(f"Error processing invoice from URI {uri}: {str(e)}")
            return []


    def process_invoice_pdfs_url(self, uri: str) -> List[Dict]:
        """Process invoice."""
        print(f"\n{'='*60}")
        print(f"Processing invoice")
        print(f"{'='*60}")
    
        
        results = []
        response = requests.get(uri, timeout=30).content
        pdf_document = fitz.open("pdf", response)
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document[page_num].get_pixmap(matrix=fitz.Matrix(200/72, 200/72)).tobytes("ppm")
            base64_pdf = base64.standard_b64encode(page).decode("utf-8")

            invoice_data = self.invoice_extractor.extract_invoice_info_simple(base64_pdf)
            
            if invoice_data:
                validation = self.invoice_validator.validate_zatca_compliance(invoice_data)
                
                invoice_data['processed_at'] = datetime.now().isoformat()
                invoice_data['zatca_validation'] = validation
                
                results.append(invoice_data)
            else:   
                return []
        
        # Filter results to only show complete invoices
        complete_results = self.invoice_validator.filter_complete_results(results)
        
        return complete_results