import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { applicationsAPI } from '../api/client';
import { format } from 'date-fns';

export default function ApplicationDetail() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  
  const [application, setApplication] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadApplication();
  }, [applicationId]);

  const loadApplication = async () => {
    try {
      const response = await applicationsAPI.getById(applicationId);
      setApplication(response.data);
    } catch (err) {
      console.error('Failed to load application', err);
    } finally {
      setIsLoading(false);
    }
  };

  const forms = [
    { number: 1, title: 'List of Projects Completed (Last 5 Years)', path: `/application/${applicationId}/form/1` },
    { number: 2, title: 'List of Ongoing Projects', path: `/application/${applicationId}/form/2` },
    { number: 3, title: 'Profile of Ongoing Projects', path: `/application/${applicationId}/form/3` },
    { number: 4, title: 'Total Management and Supervisory Personnel', path: `/application/${applicationId}/form/4` },
    { number: 5, title: 'Resume of Management and Supervisory Personnel', path: `/application/${applicationId}/form/5` },
    { number: 6, title: 'Total Skilled and Unskilled Manpower', path: `/application/${applicationId}/form/6` },
    { number: 7, title: 'List of Equipment and Tools', path: `/application/${applicationId}/form/7` },
    { number: 8, title: 'Project-Specific Questionnaire', path: `/application/${applicationId}/form/8` }
  ];

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-500">Application not found</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-xl font-bold text-gray-900">Application Details</h1>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Application Info */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                {application.project?.project_name}
              </h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Project Code: {application.project?.project_code}
              </p>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Status</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${
                      application.status === 'draft' ? 'bg-gray-100 text-gray-800' :
                      application.status === 'submitted' ? 'bg-blue-100 text-blue-800' :
                      application.status === 'under_review' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {application.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Created</dt>
                  <dd className="mt-1 text-sm text-gray-900">
                    {format(new Date(application.created_at), 'MMMM dd, yyyy')}
                  </dd>
                </div>
                {application.submitted_at && (
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Submitted</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {format(new Date(application.submitted_at), 'MMMM dd, yyyy')}
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>

          {/* Forms List */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Application Forms
              </h3>
              <p className="mt-1 max-w-2xl text-sm text-gray-500">
                Complete all required forms to submit your application
              </p>
            </div>
            <div className="border-t border-gray-200">
              <ul className="divide-y divide-gray-200">
                {forms.map((form) => (
                  <li key={form.number}>
                    <button
                      onClick={() => !form.disabled && navigate(form.path)}
                      disabled={form.disabled}
                      className={`w-full text-left px-4 py-4 sm:px-6 hover:bg-gray-50 transition ${
                        form.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <span className="flex items-center justify-center h-10 w-10 rounded-full bg-blue-100 text-blue-600 font-semibold mr-4">
                            {form.number}
                          </span>
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {form.title}
                            </p>
                            {form.disabled && (
                              <p className="text-xs text-gray-500 mt-1">Coming soon</p>
                            )}
                          </div>
                        </div>
                        {!form.disabled && (
                          <span className="text-gray-400">→</span>
                        )}
                      </div>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}