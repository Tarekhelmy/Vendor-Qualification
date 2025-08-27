import json
from PIL import Image
import os
from dotenv import load_dotenv
# Load environment variables from .env file  
load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")


class LLMInvoiceExtractor:
    """Class to extract invoice information using the Anthropic API."""
    def __init__(self, anthropic_client):
        self.anthropic_client = anthropic_client

    def extract_invoice_info_simple(self, base64_image) -> dict:
        """Extract invoice info using Anthropic API without tools."""
        try:
            prompt = """
            Please analyze this Saudi Arabian invoice and extract the following information in JSON format:

            {
                "invoice_number": "unique invoice identifier",
                "invoice_date": "date in YYYY-MM-DD format",
                "invoice_time": "time if available",
                "supplier_name": "supplier business name",
                "supplier_vat_number": "15-digit VAT number",
                "supplier_cr_number": "commercial registration number",
                "supplier_address": "full supplier address",
                "customer_name": "customer name",
                "customer_vat_number": "customer VAT if available",
                "customer_address": "customer address",
                "invoice_type": "Tax Invoice, Simplified Tax Invoice, etc.",
                "currency_code": "usually SAR",
                "total_amount_excluding_vat": "pre-tax total",
                "vat_amount": "total VAT amount",
                "total_amount_including_vat": "final total",
                "vat_breakdown_15_percent": "VAT at 15%",
                "vat_breakdown_5_percent": "VAT at 5%",
                "vat_breakdown_zero_percent": "VAT at 0%",
                "taxable_amount_15_percent": "amount subject to 15% VAT",
                "taxable_amount_5_percent": "amount subject to 5% VAT", 
                "taxable_amount_zero_percent": "amount subject to 0% VAT",
                "payment_terms": "payment conditions",
                "due_date": "payment due date",
                "qr_code_present": true/false,
                "additional_notes": "any special notes"
            }

            Important:
            - Look for both Arabic and English text
            - Saudi VAT numbers are 15 digits
            - Standard VAT rate in Saudi Arabia is 15%
            - Use "N/A" for missing text fields and "0" for missing amounts
            - Return ONLY the JSON object, no other text
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text.strip()
            
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                print("Could not extract JSON from response")
                return None
                
        except Exception as e:
            print(f"Error calling Anthropic API: {str(e)}")
            return None
        
    def validate_invoice_info_simple(self, base64_image) -> dict:
        """Extract invoice info using Anthropic API without tools."""
        try:
            prompt = """
            Please analyze this input and find out if its a complete invoice or a part of a contract and extract the following information in JSON format:

            {
                "is_invoice": true/false,
                "is_contract_information": true/false,
            }

            Important:
            - Saudi VAT numbers are 15 digits
            - for an invoice to be valid it must have the total amount including VAT and the total VAT
            - Return ONLY the JSON object, no other text
            """
            
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ]
            )
            
            # Extract JSON from response
            response_text = response.content[0].text.strip()
            
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                print("Could not extract JSON from response")
                return None
                
        except Exception as e:
            print(f"Error calling Anthropic API: {str(e)}")
            return None

    def extract_invoice_info_uri(self, uri) -> dict:
        """Extract invoice info using Anthropic API without tools."""
        try:
            prompt = """
            Please analyze this Saudi Arabian invoice and extract the following information in JSON format:

            {
                "invoice_number": "unique invoice identifier",
                "invoice_date": "date in YYYY-MM-DD format",
                "supplier_name": "supplier business name",
                "supplier_vat_number": "15-digit VAT number",
                "supplier_cr_number": "commercial registration number",
                "supplier_address": "full supplier address",
                "customer_name": "customer name",
                "customer_vat_number": "customer VAT if available",
                "customer_address": "customer address",
                "invoice_type": "Tax Invoice, Simplified Tax Invoice, etc.",
                "currency_code": "usually SAR",
                "total_amount_excluding_vat": "pre-tax total",
                "vat_amount": "total VAT amount",
                "total_amount_including_vat": "final total",
                "vat_breakdown_15_percent": "VAT at 15%",
                "vat_breakdown_5_percent": "VAT at 5%",
                "vat_breakdown_zero_percent": "VAT at 0%",
                "taxable_amount_15_percent": "amount subject to 15% VAT",
                "taxable_amount_5_percent": "amount subject to 5% VAT", 
                "taxable_amount_zero_percent": "amount subject to 0% VAT",
                "payment_terms": "payment conditions",
                "qr_code_present": true/false,
                "additional_notes": "any special notes"
            }

            Important:
            - Look for both Arabic and English text
            - Saudi VAT numbers are 15 digits
            - Standard VAT rate in Saudi Arabia is 15%
            - Use "N/A" for missing text fields and "0" for missing amounts
            - Return ONLY the JSON object, no other text
            """
            
            response = self.anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "document",
                                        "source": {
                                            "type": "url",
                                            "url": uri
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": prompt
                                    }
                                ]
                            }
                        ],
                    )

            
            # Extract JSON from response
            response_text = response.content[0].text.strip()
            print(response_text)
            # Try to find JSON in the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                print("Could not extract JSON from response")
                return None
                
        except Exception as e:
            print(f"Error calling Anthropic API: {str(e)}")
            return None

    def extract_invoice_info_pdf(self, pdf) -> dict:
            """Extract invoice info using Anthropic API without tools."""
            try:
                prompt = """
                Please analyze this Saudi Arabian invoice and extract the following information in JSON format:

                {
                    "invoice_number": "unique invoice identifier",
                    "invoice_date": "date in YYYY-MM-DD format",
                    "invoice_time": "time if available",
                    "supplier_name": "supplier business name",
                    "supplier_vat_number": "15-digit VAT number",
                    "supplier_cr_number": "commercial registration number",
                    "supplier_address": "full supplier address",
                    "customer_name": "customer name",
                    "customer_vat_number": "customer VAT if available",
                    "customer_address": "customer address",
                    "invoice_type": "Tax Invoice, Simplified Tax Invoice, etc.",
                    "currency_code": "usually SAR",
                    "total_amount_excluding_vat": "pre-tax total",
                    "vat_amount": "total VAT amount",
                    "total_amount_including_vat": "final total",
                    "vat_breakdown_15_percent": "VAT at 15%",
                    "vat_breakdown_5_percent": "VAT at 5%",
                    "vat_breakdown_zero_percent": "VAT at 0%",
                    "taxable_amount_15_percent": "amount subject to 15% VAT",
                    "taxable_amount_5_percent": "amount subject to 5% VAT", 
                    "taxable_amount_zero_percent": "amount subject to 0% VAT",
                    "payment_terms": "payment conditions",
                    "due_date": "payment due date",
                    "qr_code_present": true/false,
                    "additional_notes": "any special notes"
                }

                Important:
                - Look for both Arabic and English text
                - Saudi VAT numbers are 15 digits
                - Standard VAT rate in Saudi Arabia is 15%
                - Use "N/A" for missing text fields and "0" for missing amounts
                - Return ONLY the JSON object, no other text
                """
                
                response = self.anthropic_client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=1024,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "document",
                                            "source": {
                                            "type": "base64",
                                            "media_type": "application/pdf",
                                            "data": pdf
                                            }
                                        },
                                        {
                                            "type": "text",
                                            "text": prompt
                                        }
                                    ]
                                }
                            ],
                        )

                
                # Extract JSON from response
                response_text = response.content[0].text.strip()
                print(response_text)
                # Try to find JSON in the response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    return json.loads(json_str)
                else:
                    print("Could not extract JSON from response")
                    return None
                    
            except Exception as e:
                print(f"Error calling Anthropic API: {str(e)}")
                return None


    def count_tokens(self, content):
        prompt = """
            Please analyze this Saudi Arabian invoice and extract the following information in JSON format:

            {
                "invoice_number": "unique invoice identifier",
                "invoice_date": "date in YYYY-MM-DD format",
                "invoice_time": "time if available",
                "supplier_name": "supplier business name",
                "supplier_vat_number": "15-digit VAT number",
                "supplier_cr_number": "commercial registration number",
                "supplier_address": "full supplier address",
                "customer_name": "customer name",
                "customer_vat_number": "customer VAT if available",
                "customer_address": "customer address",
                "invoice_type": "Tax Invoice, Simplified Tax Invoice, etc.",
                "currency_code": "usually SAR",
                "total_amount_excluding_vat": "pre-tax total",
                "vat_amount": "total VAT amount",
                "total_amount_including_vat": "final total",
                "vat_breakdown_15_percent": "VAT at 15%",
                "vat_breakdown_5_percent": "VAT at 5%",
                "vat_breakdown_zero_percent": "VAT at 0%",
                "taxable_amount_15_percent": "amount subject to 15% VAT",
                "taxable_amount_5_percent": "amount subject to 5% VAT", 
                "taxable_amount_zero_percent": "amount subject to 0% VAT",
                "payment_terms": "payment conditions",
                "due_date": "payment due date",
                "qr_code_present": true/false,
                "additional_notes": "any special notes"
            }

            Important:
            - Look for both Arabic and English text
            - Saudi VAT numbers are 15 digits
            - Standard VAT rate in Saudi Arabia is 15%
            - Use "N/A" for missing text fields and "0" for missing amounts
            - Return ONLY the JSON object, no other text
            """
        
        tokens = self.anthropic_client.messages.count_tokens(
                                model="claude-sonnet-4-20250514",
                                messages=[
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "document",
                                        "source": {
                                            "type": "url",
                                            "url": content
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": prompt
                                    }
                                ]
                            }
                        ]
                            )
        return tokens.input_tokens