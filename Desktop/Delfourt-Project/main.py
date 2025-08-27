
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
# Try to import optional dependencies

def main():
    """Main function."""
    print("🇸🇦 ZATCA Invoice Extractor - Complete Data Only")
    print("=" * 55)
    print("📋 This tool only shows invoices with complete, meaningful data:")
    print("   ✅ All required fields present")
    print("   ✅ Valid amounts (> 0 SAR)")
    print("   ✅ Valid 15-digit VAT numbers")
    print("   ✅ Proper dates and names")
    print("")
    
    # Add your URIs here
    test_uri = os.getenv('TEST_INVOICE_URI')
    if not test_uri:
        print("Warning: No URI specified. Set TEST_INVOICE_URI environment variable.")
        return
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
    # Save only complete results
    if invoices:
        print(f"📊 Total complete invoices: {len(invoices)}")
        print(invoices)
    else:
        print(f"\n💡 Tips for better results:")
        print(f"   • Ensure the document contains actual invoices")
        print(f"   • Check image quality and resolution")
        print(f"   • Verify the document is in Arabic/English")
        print(f"   • Make sure amounts and VAT numbers are clearly visible")

if __name__ == "__main__":
    main()