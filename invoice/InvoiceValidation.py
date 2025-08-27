from typing import List, Dict, Optional


class InvoiceValidator:
    """Class to extract invoice information using the Anthropic API."""
    def __init__(self):
        """Initialize the ImageProcessing class."""
        pass

    def validate_zatca_compliance(self, invoice_data: Dict) -> Dict:
        """Validate ZATCA compliance."""
        validation = {
            "is_compliant": True,
            "warnings": [],
            "errors": []
        }
        
        # Check VAT number format
        vat_number = invoice_data['supplier_vat_number']
        if vat_number and vat_number != 'N/A':
            clean_vat = vat_number.replace(' ', '').replace('-', '')
            if not (clean_vat.isdigit() and len(clean_vat) == 15):
                validation["errors"].append(f"Invalid VAT number: {vat_number}")
                validation["is_compliant"] = False
        
        # Check currency
        currency = invoice_data['currency_code']
        if currency and currency != 'SAR':
            validation["warnings"].append(f"Currency is {currency}, expected SAR")
        
        # Check QR code
        if not invoice_data['qr_code_present'] or invoice_data['qr_code_present'] == 'N/A':
            validation["warnings"].append("No QR code detected - required by ZATCA")
        
        # Check VAT calculation consistency
        try:
            total_excl = float(str(invoice_data['total_amount_excluding_vat']).replace('SAR', '').replace(',', '').strip())
            vat_amt = float(str(invoice_data['vat_amount']).replace('SAR', '').replace(',', '').strip())
            total_incl = float(str(invoice_data['total_amount_including_vat']).replace('SAR', '').replace(',', '').strip())
            
            if abs((total_excl + vat_amt) - total_incl) > 0.01:
                validation["warnings"].append(f"VAT calculation may be incorrect: {total_excl} + {vat_amt} ≠ {total_incl}")
        except (ValueError, TypeError):
            validation["warnings"].append("Could not validate VAT calculations")
        
        return validation
    
    def is_complete_invoice_data(self,invoice_data: Dict) -> bool:
        """
        Check if invoice data is complete and meaningful.
        Returns True only if all essential fields have real values.
        """
        # Required fields that must not be empty or N/A
        required_fields = [
            'invoice_number',
            'invoice_date', 
            'supplier_name',
            'supplier_vat_number',
            'customer_name'
        ]
        
        # Check required fields
        for field in required_fields:
            value = str(invoice_data[field]).strip()
            if not value or value.upper() in ['N/A', 'NA', 'NULL', 'NONE', '']:
                print(f"❌ Missing required field: {field} = '{value}'")
                return False
        
        # Check financial amounts - at least one must be meaningful
        financial_fields = [
            'total_amount_excluding_vat',
            'vat_amount', 
            'total_amount_including_vat'
        ]
        
        has_meaningful_amount = False
        for field in financial_fields:
            value = str(invoice_data[field]).strip()
            # Remove currency symbols and whitespace
            clean_value = value.replace('SAR', '').replace(',', '').strip()
            
            try:
                amount = float(clean_value)
                if amount > 0:
                    has_meaningful_amount = True
                    break
            except (ValueError, TypeError):
                continue
        
        if not has_meaningful_amount:
            print("❌ No meaningful financial amounts found")
            return False
        
        # Check VAT number format (should be 15 digits for Saudi Arabia)
        vat_number = str(invoice_data['supplier_vat_number']).strip()
        clean_vat = vat_number.replace(' ', '').replace('-', '')
        if not (clean_vat.isdigit() and len(clean_vat) == 15):
            print(f"❌ Invalid VAT number format: '{vat_number}' (should be 15 digits)")
            return False
        
        # Check date format
        invoice_date = str(invoice_data['invoice_date']).strip()
        if invoice_date.upper() in ['N/A', 'NA']:
            print(f"❌ Invalid date: '{invoice_date}'")
            return False
        
        # Additional validation for meaningful data
        supplier_name = str(invoice_data['supplier_name']).strip()
        if len(supplier_name) < 3:
            print(f"❌ Supplier name too short: '{supplier_name}'")
            return False
        
        customer_name = str(invoice_data['customer_name']).strip()
        if len(customer_name) < 2:
            print(f"❌ Customer name too short: '{customer_name}'")
            return False
        
        print(f"✅ Invoice data is complete and valid")
        return True
    
    def filter_complete_results(self,results: List[Dict]) -> List[Dict]:
        """Filter results to only include complete invoices."""
        if not results:
            return []
        
        print(f"\n🔍 Filtering {len(results)} results for completeness...")
        
        complete_results = []
        for i, result in enumerate(results):
            print(f"\nValidating result {i+1}:")
            if self.is_complete_invoice_data(result):
                complete_results.append(result)
            else:
                print(f"❌ Result {i+1} excluded due to incomplete data")
        
        print(f"\n✅ {len(complete_results)} out of {len(results)} results have complete data")
        return complete_results