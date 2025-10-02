import time
import os
from invoice.FileProcessing import FileProcessor
from invoice.InvoiceProcessing import InvoiceProcessor
from Supabase import SupabaseClient

from contract.ContractProcessing import ContractProcessor

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