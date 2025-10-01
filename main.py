
"""
Simplified ZATCA Invoice Information Extractor
Minimal dependencies version to avoid conflicts.

Required installations:
pip install anthropic pillow requests python-dotenv

Optional (for PDF support):
pip install PyMuPDF

Optional (for image enhancement):  
pip install opencv-python
"""
import time
import os
from invoice.FileProcessing import FileProcessor
from invoice.InvoiceProcessing import InvoiceProcessor
from Supabase import SupabaseClient

from contract.ContractProcessing import ContractProcessor
# Try to import optional dependencies

def invoiceProcess():
    """Main function."""

    file_processor = FileProcessor()
    invoice_processor = InvoiceProcessor()
    supabase_client = SupabaseClient()
    projects = supabase_client.get_previous_projects()
    if not projects:
        print("❌ No projects found in the database.")
        return
    
    invoices = []
    for project in projects:
        base64_images = file_processor.process_file_from_uri(project['file_uri'])
        invoices = invoice_processor.process_invoice_base64_images(base64_images)
        if len(invoices) > 1:
            total_amount = sum(float(invoice.get('total_amount_including_vat', 0)) for invoice in invoices)
        else:
            total_amount = float(invoices[0].get('total_amount_including_vat', 0)) if invoices else 0
        if total_amount == project['total_amount_including_vat']:
            print(f"✅ Project {project['id']} matches total amount: {total_amount} SAR")
            supabase_client.update_project_verification(project['id'], True)
        else:
            print(f"❌ Project {project['id']} total amount mismatch: {total_amount} SAR vs {project['total_amount_including_vat']} SAR")
            supabase_client.update_project_verification(project['id'], False)
        time.sleep(60)  # Sleep to avoid rate limits

    if not invoices:
        print("❌ No invoices found or processed.")
        return
    
def contractProcess():
    """Main function."""
    contract_processor = ContractProcessor()
    supabase_client = SupabaseClient()
    projects = supabase_client.get_previous_projects()
    if not projects:
        print("❌ No projects found in the database.")
        return
    
    contracts = []
    for project in projects:
        contracts = contract_processor.process_contract(project)
        if contracts and contracts['is_valid']:
            print(f"✅ Project {project['id']} contract is valid.")
            supabase_client.update_project_verification(project['id'],file_verified= contracts['is_valid'], verification_comment=contracts['reason'])
        else:
            print(f"❌ Project {project['id']} contract is invalid.")
            supabase_client.update_project_verification(project['id'], False, "Invalid contract data")

    if not contracts:
        print("❌ No contracts found or processed.")
        return

if __name__ == "__main__":
    contractProcess()