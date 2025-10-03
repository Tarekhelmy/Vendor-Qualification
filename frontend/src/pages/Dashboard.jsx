import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import { applicationsAPI, projectsAPI, profileAPI } from '../api/client';
import { format } from 'date-fns';
import NotificationBell from '../components/NotificationBell';

export default function Dashboard() {
    const { vendor, logout } = useAuthStore();
    const navigate = useNavigate();
    
    const [applications, setApplications] = useState([]);
    const [availableProjects, setAvailableProjects] = useState([]);
    const [profileComplete, setProfileComplete] = useState(true); // Add this state
    const [isLoading, setIsLoading] = useState(true);
    const [showNewAppModal, setShowNewAppModal] = useState(false);
    const [selectedProject, setSelectedProject] = useState('');
    const [error, setError] = useState('');
  
    useEffect(() => {
      loadData();
      checkProfileCompletion(); // Add this
    }, []);
  
    const loadData = async () => {
      try {
        setIsLoading(true);
        const [appsRes, projsRes] = await Promise.all([
          applicationsAPI.getAll(),
          projectsAPI.getAvailableProjects()
        ]);
        
        setApplications(appsRes.data);
        setAvailableProjects(projsRes.data);
      } catch (err) {
        setError('Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };
  
    // Add this function
    const checkProfileCompletion = async () => {
      try {
        const response = await profileAPI.getProfile();
        setProfileComplete(response.data.profile_complete);
      } catch (err) {
        console.error('Failed to check profile completion:', err);
      }
    };

  const handleCreateApplication = async () => {
    if (!selectedProject) {
      setError('Please select a project');
      return;
    }

    try {
      const response = await applicationsAPI.create(selectedProject);
      setApplications([response.data, ...applications]);
      setShowNewAppModal(false);
      setSelectedProject('');
      setError('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create application');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      draft: 'bg-gray-100 text-gray-800',
      submitted: 'bg-blue-100 text-blue-800',
      under_review: 'bg-yellow-100 text-yellow-800',
      reviewed: 'bg-green-100 text-green-800',
    };

    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${styles[status]}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
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
              <h1 className="text-xl font-bold text-gray-900">Vendor Portal</h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* Profile Card Button with Warning */}
              <button
                onClick={() => navigate('/profile')}
                className="relative flex items-center space-x-3 px-4 py-2 rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 transition-all duration-200 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
              >
                {/* Warning Badge */}
                {!profileComplete && (
                  <div className="absolute -top-1 -right-1 h-6 w-6 bg-red-500 rounded-full flex items-center justify-center animate-pulse">
                    <span className="text-white text-xs font-bold">!</span>
                  </div>
                )}
                
                <div className="flex items-center justify-center h-8 w-8 rounded-full bg-white bg-opacity-20">
                  <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div className="text-left">
                  <p className="text-xs text-blue-100">Profile</p>
                  <p className="text-sm font-semibold text-white">{vendor?.company_name}</p>
                </div>
              </button>

              {/* Logout Button */}
              <NotificationBell />
              <button
                onClick={logout}
                className="text-sm text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md hover:bg-gray-100 transition"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Welcome Section */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900">Welcome, {vendor?.contact_person_name}</h2>
            <p className="mt-1 text-sm text-gray-600">
            Manage Your Company's Applications
            </p>
          </div>

          {/* New Application Button */}
          <div className="mb-6">
            <button
              onClick={() => setShowNewAppModal(true)}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              + New Application
            </button>
          </div>

          {/* Applications List */}
          {applications.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No applications yet. Create your first application to get started.</p>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {applications.map((app) => (
                  <li key={app.id}>
                    <div
                      onClick={() => navigate(`/application/${app.id}`)}
                      className="block hover:bg-gray-50 cursor-pointer"
                    >
                      <div className="px-4 py-4 sm:px-6">
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-blue-600 truncate">
                              {app.project?.project_name}
                            </p>
                            <p className="mt-1 text-sm text-gray-500">
                              Project Code: {app.project?.project_code}
                            </p>
                          </div>
                          <div className="ml-4 flex-shrink-0">
                            {getStatusBadge(app.status)}
                          </div>
                        </div>
                        <div className="mt-2 flex justify-between">
                          <p className="text-xs text-gray-500">
                            Created: {format(new Date(app.created_at), 'MMM dd, yyyy')}
                          </p>
                          {app.submitted_at && (
                            <p className="text-xs text-gray-500">
                              Submitted: {format(new Date(app.submitted_at), 'MMM dd, yyyy')}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* New Application Modal */}
      {showNewAppModal && (
        <div className="fixed z-10 inset-0 overflow-y-auto">
          <div className="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
            <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={() => setShowNewAppModal(false)}></div>

            <div className="inline-block align-bottom bg-white rounded-lg px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6">
              <div>
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  Create New Application
                </h3>
                
                {error && (
                  <div className="mb-4 rounded-md bg-red-50 p-4">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                )}

                <div>
                  <label htmlFor="project" className="block text-sm font-medium text-gray-700">
                    Select Project
                  </label>
                  <select
                    id="project"
                    value={selectedProject}
                    onChange={(e) => setSelectedProject(e.target.value)}
                    className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
                  >
                    <option value="">-- Select a project --</option>
                    {availableProjects.map((project) => (
                      <option key={project.id} value={project.id}>
                        {project.project_name} ({project.project_code})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="mt-5 sm:mt-6 sm:grid sm:grid-cols-2 sm:gap-3 sm:grid-flow-row-dense">
                <button
                  type="button"
                  onClick={handleCreateApplication}
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:col-start-2 sm:text-sm"
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowNewAppModal(false);
                    setError('');
                    setSelectedProject('');
                  }}
                  className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 sm:mt-0 sm:col-start-1 sm:text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}