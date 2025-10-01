from supabase import create_client, Client
from dotenv import load_dotenv
import os
load_dotenv()

class SupabaseClient:   
    """Class to interact with Supabase database."""
    
    def __init__(self):
        """Initialize the Supabase client."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and Key must be set in environment variables.")
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def get_previous_projects(self) -> list:
        """Retrieve all invoices from the Supabase database."""
        response = self.client.table('contractor_completed_projects').select('*').is_('file_verified', "null").execute()
        return response.data
    
    def update_project_verification(self, project_id: str, file_verified: bool, verification_comment: str) -> None:
        """Update the file verification status of a project."""
        response = self.client.table('contractor_completed_projects').update({'file_verified': file_verified, 'verification_comment': verification_comment}).eq('id', project_id).execute()

        return response.data

if __name__ == "__main__":
    # Example usage
    supabase_client = SupabaseClient()
    try:
        previous_projects = supabase_client.get_previous_projects()
        print(f"Retrieved {len(previous_projects)} projects")
        for project in previous_projects:
            print(project)
    except Exception as e:
        print(f"Error: {str(e)}")