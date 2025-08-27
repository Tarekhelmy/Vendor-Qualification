
from Gemeni import GemeniLLMContractInfoExtractor
from ContractValidator import ContractValidator

class InvoiceProcessor:
    """Class to extract invoice information using the Anthropic API."""
    def __init__(self):
        """Initialize the ImageProcessing class."""
        self.contract_validator = ContractValidator()
        self.contract_data_extractor = GemeniLLMContractInfoExtractor()
        pass

    def extract_contract_info_uri(self, uri):
        """Process Contract."""
        print(f"\n{'='*60}")
        print(f"Extracting Contract")
        print(f"{'='*60}")
        if not uri:
            print("No URI provided")
            return []

        try:
            contract_data = self.contract_data_extractor.extract_invoice_info_uri(uri)
            print(f"Extracted contract data: {contract_data}")
            if contract_data:
                return [contract_data]
                
            else:
                print("No contract data extracted.")
                return []
                
        except Exception as e:
            print(f"Error processing invoice from URI {uri}: {str(e)}")
            return []
    
    def validate_contract(self, contract_data: dict, expected_amount: float) -> dict:
        """Validate contract data."""
        print(f"\n{'='*60}")
        print(f"Validating Contract")
        print(f"{'='*60}")
        validate_expected_amount = self.contract_validator.is_contract_amount_matching(contract_data, expected_amount)
        validate_completness = self.contract_validator.is_complete_contract_data(contract_data)
        return all([validate_expected_amount, validate_completness])
    
    def process_contract(self, project_data: dict) -> dict:
        """Process contract."""
        contract_results = self.extract_contract_info_uri(project_data)
        if not contract_results:
            print("No contract data extracted.")
            return {"is_valid": False, "contract_data": None}
        
        expected_amount = project_data.get("contract_value_sar")
        expected_contracing_company = project_data.get("contracting_company")
        expected_contracted_company = project_data.get("contracted_company")
        expected_contract_date = project_data.get("contract_date")
        expected_data = {
            "contracting_company": expected_contracing_company,
            "contracted_company": expected_contracted_company,
            "contract_date": expected_contract_date,
            "contract_total_amount": expected_amount,
            "currency": "SAR"
        }
        
        contract_data = contract_results
        contractValidation = self.compare_contract_info(contract_data, expected_data)
        return {"is_valid": contractValidation.is_matching, 
                "reason":contractValidation.reason,  
                "contract_data": contract_data}