from google import genai
from google.genai import types
import httpx
import json
import os
from dotenv import load_dotenv
from pydantic import BaseModel


class ContractValidation(BaseModel):
    is_matching: bool
    reason: str

class ContractData(BaseModel):
    contracted_company: str
    contracting_company: str
    contract_date: str
    contract_total_amount: str
    currency: str



class GemeniLLMContractInfoExtractor:
    """Class to extract invoice information using the Anthropic API."""
    def __init__(self):
        # Load environment variables from .env file  
        load_dotenv()
        api_key = os.getenv("GEMENI_API_KEY")
        self.gemeni_client = genai.Client(api_key=api_key)
        pass
    def extract_invoice_info_uri(self, file_uri: str) -> ContractData:
        """Extract invoice information from image URI using Anthropic API."""
        try:
            prompt = (
                "Extract the following fields from the contract\n"
                "- contracted_company\n"
                "- contracting_company\n"
                "- contract_cate\n"
                "- contract_total_amount\n"
                "- currency\n"
                "Return the information in JSON format."
            )
            doc_data = httpx.get(file_uri).content
            
            response = self.gemeni_client.models.generate_content(
              model="gemini-2.5-flash",
              contents=[
                    types.Part.from_bytes(
                    data=doc_data,
                    mime_type='application/pdf',
                  ),
                  prompt],
              config={
              "response_mime_type": "application/json",
              "response_schema": ContractData,}
              ,)
            print("Raw response:", response.text)
            if response.parsed:
              contract_data: ContractData = response.parsed
              return contract_data
            else:
              print("Failed to parse response")
              return None
        except Exception as e:
            print(f"Error extracting contract info: {str(e)}")
            return None

    def compare_contract_info(self, extracted_data: dict, expected_data: dict) -> ContractValidation:
        """Compare extracted contract data with expected data."""
        try:
          prompt = (
              f"Compare the following extracted contract data with the expected data.\n"
              f"Extracted Data: {json.dumps(extracted_data)}\n"
              f"Expected Data: {json.dumps(expected_data)}\n"
              f"Check if the parties involved in the contract have a name matching within a reasonable similarity indicating that the same entities are involved.\n"
              f"Check if the contract date is within a year of the expected date.\n"
              f"Check if the contract total amount matches the expected amount within a tolerance of 1000 SAR.\n"
              f"Check if the currency is SAR or USD (if USD, convert to SAR using a rate of 1 USD = 3.75 SAR for comparison).\n"
              f"if there is no match, then return the reason"
          )
          
          response = self.gemeni_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
              "response_mime_type": "application/json",
              "response_schema": ContractValidation,}
              ,)
          print("Raw response:", response.text)
          # Parse JSON response
          if response.parsed:
              contract_data: ContractValidation = response.parsed
              return contract_data
          else:
            print("Failed to parse response")
            return None
        except Exception as e:
            print(f"Error Validating Contract: {str(e)}")
            return None