
from typing import Dict

class ContractValidator:
    def __init__(self):
        """Initialize the ImageProcessing class."""
        pass

    def is_complete_contract_data(self, contract_data: Dict) -> bool:
        """
        Check if contract data is complete and meaningful.
        Returns True only if all essential fields have real values.
        """
        # Required fields that must not be empty or N/A
        required_fields = [
            'Contracted_Company',
            'Contracting_Company',
            'Contract_Date',
            'Contract_Total_Amount'
            'Currency'
        ]
        
        for field in required_fields:
            value = contract_data.get(field, '').strip()
            if not value or value.upper() == 'N/A':
                return False
        
        return True
    
    def is_contract_amount_matching(self, contract_data: Dict, expected_amount: float) -> bool:
        """
        Check if the contract total amount matches the expected amount.
        """
        try:
            if contract_data.get('Currency', '').strip().upper() == 'SAR':
                print("Currency is  SAR, as expected")
                amount_str = str(contract_data.get('Contract_Total_Amount', '')).replace('SAR', '').replace(',', '').strip()
                amount = float(amount_str)
                return abs(amount - expected_amount) < 1000  # Allow small tolerance
            elif contract_data.get('Currency', '').strip().upper() == 'USD':
                print("Converting USD to SAR for comparison")
                amount_str = str(contract_data.get('Contract_Total_Amount', '')).replace('SAR', '').replace(',', '').strip()
                amount = float(amount_str) * 3.75  # Convert USD to SAR
                return abs(amount - expected_amount) < 1000
            else:
                print(f"Unsupported currency: {contract_data.get('Currency', '')}")
                return False
            
        except (ValueError, TypeError):
            return False
