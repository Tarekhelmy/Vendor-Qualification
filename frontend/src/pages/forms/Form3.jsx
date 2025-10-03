import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { form3API } from '../../api/client';
import { useConfirm } from '../../hooks/useConfirm';

export default function Form3() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const [expandedProfiles, setExpandedProfiles] = useState({}); // New state to track expansion
  const [ongoingProjects, setOngoingProjects] = useState([]);
  const { confirm, ConfirmDialog } = useConfirm();
  const [profiles, setProfiles] = useState([]);
  const [formSubmission, setFormSubmission] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');
  const [error, setError] = useState('');

  const toggleProfileExpansion = (profileId, isExpanded) => {
    setExpandedProfiles(prev => ({
      ...prev,
      [profileId]: isExpanded,
    }));
  };
  
  const loadFormData = async (showLoadingSpinner = true) => {
    try {
      // Only set loading state if showLoadingSpinner is true
      if (showLoadingSpinner) { 
        setIsLoading(true);
      }
      const response = await form3API.getData(applicationId);
      setOngoingProjects(response.data.ongoing_projects);
      setProfiles(response.data.profiles);
      setFormSubmission(response.data.form_submission);
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load form data';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      console.error(err);
    } finally {
      // Only set loading state if showLoadingSpinner is true
      if (showLoadingSpinner) {
        setIsLoading(false);
      }
    }
  };

  useEffect(() => {
    loadFormData(true); // Initial load shows spinner
  }, [applicationId]);


  const showSaveStatus = (status) => {
    setSaveStatus(status);
    if (status === 'saved') {
      setTimeout(() => setSaveStatus(''), 2000);
    }
  };

  const handleCreateProfile = async (projectId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const project = ongoingProjects.find(p => p.id === projectId);
    if (!project) return;

    const newProfile = {
      ongoing_project_id: projectId,
      contract_number: project.contract_number || null,
      client_name: project.client_name || null,
      contract_title: project.project_title || null,
      contract_value_sar: project.contract_value_sar || null,
      percent_completion: project.percent_completion || null,
      contractor_role: 'Main Contractor',
      management_count: 0,
      supervisory_count: 0,
      skilled_count: 0,
      unskilled_count: 0,
    };

    try {
      setSaveStatus('saving');
      setError('');
      const response = await form3API.createProfile(applicationId, newProfile);
      setProfiles([...profiles, response.data]);
      
      // Update ongoing projects list
      setOngoingProjects(prev =>
        prev.map(p => p.id === projectId ? { ...p, has_profile: true, profile_id: response.data.id } : p)
      );
      
      showSaveStatus('saved');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to create profile';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      setSaveStatus('');
      console.error('Create profile error:', err.response?.data);
    }
  };

  const handleUpdateProfile = useCallback(async (profileId, field, value) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    // Update local state immediately
    setProfiles(prev => 
      prev.map(p => p.id === profileId ? { ...p, [field]: value } : p)
    );

    setSaveStatus('saving');
    
    try {
      const updateData = { [field]: value };
      await form3API.updateProfile(profileId, updateData);
      showSaveStatus('saved');
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save changes';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to save changes');
      setSaveStatus('');
      console.error('Update error:', err.response?.data);
    }
  }, [applicationId, formSubmission]);

  const handleDeleteProfile = async (profileId, ongoingProjectId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const confirmed = await confirm({
        title: "Delete Project",
        message: "Are you sure you want to delete this profile?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
      if (!confirmed) return;

    try {
      await form3API.deleteProfile(profileId);
      setProfiles(profiles.filter(p => p.id !== profileId));
      
      // Update ongoing projects list
      setOngoingProjects(prev =>
        prev.map(p => p.id === ongoingProjectId ? { ...p, has_profile: false, profile_id: null } : p)
      );
      
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete profile';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete profile');
    }
  };

  const handleSubmitForm = async () => {
    if (profiles.length === 0) {
      setError('Please create at least one project profile before submitting');
      return;
    }
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Are you sure you want to submit this form? It will be locked after submission.",
        confirmText: "Submit",
        cancelText: "Cancel",
        type: "warning"
      });
    if (!confirmed) return;


    try {
      setIsSaving(true);
      setError('');
      const response = await form3API.submit(applicationId);
      setFormSubmission(response.data);
      alert('Form submitted successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to submit form';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to submit form');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const projectsWithoutProfiles = ongoingProjects.filter(p => !p.has_profile);

  return (
    <div className="min-h-screen bg-gray-50">
        {/* This line renders the confirmation modal */}
      <ConfirmDialog />
      {/* Header */}
      <nav className="bg-white shadow sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate(`/application/${applicationId}`)}
                className="text-gray-600 hover:text-gray-900 mr-4"
              >
                ← Back
              </button>
              <h1 className="text-lg font-bold text-gray-900">
                Form 3: Profile of Ongoing Projects
              </h1>
            </div>
            <div className="flex items-center space-x-3">
              {saveStatus === 'saving' && (
                <span className="text-sm text-gray-500">Saving...</span>
              )}
              {saveStatus === 'saved' && (
                <span className="text-sm text-green-600">✓ Saved</span>
              )}
              {formSubmission?.is_locked && (
                <span className="px-3 py-1 text-sm bg-yellow-100 text-yellow-800 rounded-full">
                  🔒 Locked
                </span>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Info Banner */}
          {ongoingProjects.length === 0 && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                No ongoing projects found. Please complete Form 2 first to add ongoing projects before creating profiles.
              </p>
            </div>
          )}

          {/* Available Projects to Profile */}
          {!formSubmission?.is_locked && projectsWithoutProfiles.length > 0 && (
            <div className="mb-6 bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Available Projects (Select to Create Profile)
              </h3>
              <div className="space-y-3">
                {projectsWithoutProfiles.map((project) => (
                  <div
                    key={project.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {project.project_title}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Client: {project.client_name} | Type: {project.project_field}
                        </p>
                        {project.contract_number && (
                          <p className="text-xs text-gray-500">
                            Contract: {project.contract_number}
                          </p>
                        )}
                      </div>
                      <button
                        onClick={() => handleCreateProfile(project.id)}
                        className="ml-4 px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      >
                        + Create Profile
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Profiles List */}
          {profiles.length === 0 && ongoingProjects.length > 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No project profiles created yet. Select a project above to create a profile.</p>
            </div>
          ) : profiles.length === 0 ? null : (
            <div className="space-y-6">
              {profiles.map((profile, index) => {
                const relatedProject = ongoingProjects.find(p => p.id === profile.ongoing_project_id);
                return (
                <ProfileCard
                    key={profile.id}
                    profile={profile}
                    relatedProject={relatedProject}
                    index={index}
                    isLocked={formSubmission?.is_locked}
                    onUpdate={handleUpdateProfile}
                    onDelete={handleDeleteProfile}
                    onRefresh={() => loadFormData(false)} // Use loadFormData(false) for local list updates
                    // New Props
                    isExpanded={expandedProfiles[profile.id] || false} // Pass current state
                    onToggleExpand={toggleProfileExpansion} // Pass toggler function
                />
                );
            })}
            </div>
          )}

          {/* Submit Button */}
          {!formSubmission?.is_locked && profiles.length > 0 && (
            <div className="mt-8 flex justify-end">
              <button
                onClick={handleSubmitForm}
                disabled={isSaving}
                className="px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 disabled:opacity-50"
              >
                {isSaving ? 'Submitting...' : 'Submit Form'}
              </button>
            </div>
          )}

          {formSubmission?.is_locked && (
            <div className="mt-8 p-4 bg-yellow-50 rounded-md">
              <p className="text-sm text-yellow-800">
                This form has been submitted and is locked. Contact support if you need to make changes.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Profile Card Component
function ProfileCard({ profile, relatedProject, index, isLocked, onUpdate, onDelete, onRefresh, isExpanded, onToggleExpand  }) {
//   const [isExpanded, setIsExpanded] = useState(false);

const handleToggle = () => {
    onToggleExpand(profile.id, !isExpanded);
};
  const handleFieldChange = (field, value) => {
    onUpdate(profile.id, field, value);
  };

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900">
              Profile {index + 1}: {profile.contract_title || relatedProject?.project_title || 'Project Profile'}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Client: {profile.client_name} {profile.contract_number && `| Contract: ${profile.contract_number}`}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {!isLocked && (
              <button
                onClick={() => onDelete(profile.id, profile.ongoing_project_id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete
              </button>
            )}
            <button
            onClick={handleToggle} // Call the new handler
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
        >
            {isExpanded ? 'Collapse' : 'Expand'}
        </button>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="px-6 py-4 space-y-6">
          {/* Basic Project Information */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">Project Information</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Contract Signed Date</label>
                <input
                  type="date"
                  value={profile.contract_signed_date || ''}
                  onChange={(e) => handleFieldChange('contract_signed_date', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Completion Date</label>
                <input
                  type="date"
                  value={profile.completion_date || ''}
                  onChange={(e) => handleFieldChange('completion_date', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Forecasted Completion Date</label>
                <input
                  type="date"
                  value={profile.forecasted_completion_date || ''}
                  onChange={(e) => handleFieldChange('forecasted_completion_date', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Percent Completion (%)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="100"
                  value={profile.percent_completion || ''}
                  onChange={(e) => handleFieldChange('percent_completion', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Contract Type</label>
                <input
                  type="text"
                  value={profile.contract_type || ''}
                  onChange={(e) => handleFieldChange('contract_type', e.target.value)}
                  disabled={isLocked}
                  placeholder="e.g., Frame Contract"
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Contract Value (SAR)</label>
                <input
                  type="number"
                  step="0.01"
                  value={profile.contract_value_sar || ''}
                  onChange={(e) => handleFieldChange('contract_value_sar', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Contractor Role</label>
                <select
                  value={profile.contractor_role || 'Main Contractor'}
                  onChange={(e) => handleFieldChange('contractor_role', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                >
                  <option value="Main Contractor">Main Contractor</option>
                  <option value="Subcontractor">Subcontractor</option>
                </select>
              </div>
            </div>
          </div>

          {/* Representative Information */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">Representative Information</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Representative Name</label>
                <input
                  type="text"
                  value={profile.representative_name || ''}
                  onChange={(e) => handleFieldChange('representative_name', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Position</label>
                <input
                  type="text"
                  value={profile.representative_position || ''}
                  onChange={(e) => handleFieldChange('representative_position', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Telephone Number</label>
                <input
                  type="tel"
                  value={profile.representative_phone || ''}
                  onChange={(e) => handleFieldChange('representative_phone', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Manpower Counts */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">Number of Manpower Assigned</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Management</label>
                <input
                  type="number"
                  min="0"
                  value={profile.management_count || 0}
                  onChange={(e) => handleFieldChange('management_count', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Supervisory</label>
                <input
                  type="number"
                  min="0"
                  value={profile.supervisory_count || 0}
                  onChange={(e) => handleFieldChange('supervisory_count', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Skilled</label>
                <input
                  type="number"
                  min="0"
                  value={profile.skilled_count || 0}
                  onChange={(e) => handleFieldChange('skilled_count', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Unskilled</label>
                <input
                  type="number"
                  min="0"
                  value={profile.unskilled_count || 0}
                  onChange={(e) => handleFieldChange('unskilled_count', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>
            </div>
          </div>

          {/* Lists */}
          <PersonnelList profileId={profile.id} personnel={profile.personnel || []} isLocked={isLocked} onRefresh={onRefresh} />
          <EquipmentList profileId={profile.id} equipment={profile.equipment || []} isLocked={isLocked} onRefresh={onRefresh} />
          <MaterialsList profileId={profile.id} materials={profile.materials || []} isLocked={isLocked} onRefresh={onRefresh} />
          <SubcontractorsList profileId={profile.id} subcontractors={profile.subcontractors || []} isLocked={isLocked} onRefresh={onRefresh} />
        </div>
      )}
    </div>
  );
}

// Personnel List Component
function PersonnelList({ profileId, personnel, isLocked, onRefresh }) {
  const [isAdding, setIsAdding] = useState(false);
  const [newItem, setNewItem] = useState({ position: '', name: '' });

  const handleAdd = async () => {
    if (!newItem.position || !newItem.name) {
      alert('Please fill in both position and name');
      return;
    }

    try {
      await form3API.addPersonnel(profileId, newItem);
      setNewItem({ position: '', name: '' });
      setIsAdding(false);
      onRefresh();
    } catch (err) {
      alert('Failed to add personnel');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Delete this personnel entry?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;
    try {
      await form3API.deletePersonnel(id);
      onRefresh();
    } catch (err) {
      alert('Failed to delete personnel');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-medium text-gray-900">Management & Supervisory Personnel</h4>
        {!isLocked && !isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            + Add Personnel
          </button>
        )}
      </div>

      {isAdding && (
        <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
          <div className="grid grid-cols-2 gap-2 mb-2">
            <input
              type="text"
              placeholder="Position (e.g., Project Manager)"
              value={newItem.position}
              onChange={(e) => setNewItem({ ...newItem, position: e.target.value })}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <input
              type="text"
              placeholder="Name"
              value={newItem.name}
              onChange={(e) => setNewItem({ ...newItem, name: e.target.value })}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleAdd}
              className="px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700"
            >
              Save
            </button>
            <button
              onClick={() => {
                setIsAdding(false);
                setNewItem({ position: '', name: '' });
              }}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {personnel.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No personnel added</p>
      ) : (
        <div className="space-y-2">
          {personnel.map(item => (
            <div key={item.id} className="flex justify-between items-center p-3 bg-gray-50 rounded">
              <div className="text-sm">
                <span className="font-medium text-gray-900">{item.position}</span>
                <span className="text-gray-600"> - {item.name}</span>
              </div>
              {!isLocked && (
                <button
                  onClick={() => handleDelete(item.id)}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Delete
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Equipment List Component
function EquipmentList({ profileId, equipment, isLocked, onRefresh }) {
  const [isAdding, setIsAdding] = useState(false);
  const [newItem, setNewItem] = useState('');

  const handleAdd = async () => {
    if (!newItem.trim()) {
      alert('Please enter equipment name');
      return;
    }

    try {
      await form3API.addEquipment(profileId, { equipment_name: newItem });
      setNewItem('');
      setIsAdding(false);
      onRefresh();
    } catch (err) {
      alert('Failed to add equipment');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Delete this equipment?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;
    try {
      await form3API.deleteEquipment(id);
      onRefresh();
    } catch (err) {
      alert('Failed to delete equipment');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-medium text-gray-900">Construction Equipment & Machinery</h4>
        {!isLocked && !isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            + Add Equipment
          </button>
        )}
      </div>

      {isAdding && (
        <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
          <input
            type="text"
            placeholder="Equipment name (e.g., Trencher, Compactor)"
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md mb-2"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleAdd}
              className="px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700"
            >
              Save
            </button>
            <button
              onClick={() => {
                setIsAdding(false);
                setNewItem('');
              }}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {equipment.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No equipment added</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {equipment.map(item => (
            <span
              key={item.id}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
            >
              {item.equipment_name}
              {!isLocked && (
                <button
                  onClick={() => handleDelete(item.id)}
                  className="ml-2 text-blue-600 hover:text-blue-900 font-bold"
                >
                  ×
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// Materials List Component
function MaterialsList({ profileId, materials, isLocked, onRefresh }) {
  const [isAdding, setIsAdding] = useState(false);
  const [newItem, setNewItem] = useState('');

  const handleAdd = async () => {
    if (!newItem.trim()) {
      alert('Please enter material name');
      return;
    }

    try {
      await form3API.addMaterial(profileId, { material_name: newItem });
      setNewItem('');
      setIsAdding(false);
      onRefresh();
    } catch (err) {
      alert('Failed to add material');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Delete this material?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;
    try {
      await form3API.deleteMaterial(id);
      onRefresh();
    } catch (err) {
      alert('Failed to delete material');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-medium text-gray-900">Major Materials and Equipment</h4>
        {!isLocked && !isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            + Add Material
          </button>
        )}
      </div>

      {isAdding && (
        <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
          <input
            type="text"
            placeholder="Material name (e.g., Cables, Sand, Asphalt)"
            value={newItem}
            onChange={(e) => setNewItem(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md mb-2"
          />
          <div className="flex space-x-2">
            <button
              onClick={handleAdd}
              className="px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700"
            >
              Save
            </button>
            <button
              onClick={() => {
                setIsAdding(false);
                setNewItem('');
              }}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {materials.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No materials added</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {materials.map(item => (
            <span
              key={item.id}
              className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800"
            >
              {item.material_name}
              {!isLocked && (
                <button
                  onClick={() => handleDelete(item.id)}
                  className="ml-2 text-green-600 hover:text-green-900 font-bold"
                >
                  ×
                </button>
              )}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// Subcontractors List Component
function SubcontractorsList({ profileId, subcontractors, isLocked, onRefresh }) {
  const [isAdding, setIsAdding] = useState(false);
  const [newItem, setNewItem] = useState({ contractor_name: '', work_description: '', value_sar: '' });

  const handleAdd = async () => {
    if (!newItem.contractor_name.trim()) {
      alert('Please enter contractor name');
      return;
    }

    try {
      const data = {
        contractor_name: newItem.contractor_name,
        work_description: newItem.work_description || null,
        value_sar: newItem.value_sar ? parseFloat(newItem.value_sar) : null
      };
      await form3API.addSubcontractor(profileId, data);
      setNewItem({ contractor_name: '', work_description: '', value_sar: '' });
      setIsAdding(false);
      onRefresh();
    } catch (err) {
      alert('Failed to add subcontractor');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Delete this subcontractor?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;
    try {
      await form3API.deleteSubcontractor(id);
      onRefresh();
    } catch (err) {
      alert('Failed to delete subcontractor');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-medium text-gray-900">Subcontractors</h4>
        {!isLocked && !isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            + Add Subcontractor
          </button>
        )}
      </div>

      {isAdding && (
        <div className="mb-3 p-3 bg-gray-50 rounded border border-gray-200">
          <div className="space-y-2 mb-2">
            <input
              type="text"
              placeholder="Name of Contractor"
              value={newItem.contractor_name}
              onChange={(e) => setNewItem({ ...newItem, contractor_name: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <textarea
              placeholder="Description of Work Subcontracted"
              value={newItem.work_description}
              onChange={(e) => setNewItem({ ...newItem, work_description: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
              rows="2"
            />
            <input
              type="number"
              step="0.01"
              placeholder="Value (SAR)"
              value={newItem.value_sar}
              onChange={(e) => setNewItem({ ...newItem, value_sar: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handleAdd}
              className="px-3 py-1 text-sm text-white bg-green-600 rounded hover:bg-green-700"
            >
              Save
            </button>
            <button
              onClick={() => {
                setIsAdding(false);
                setNewItem({ contractor_name: '', work_description: '', value_sar: '' });
              }}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {subcontractors.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No subcontractors added</p>
      ) : (
        <div className="space-y-3">
          {subcontractors.map(item => (
            <div key={item.id} className="p-3 bg-gray-50 rounded border border-gray-200">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{item.contractor_name}</p>
                  {item.work_description && (
                    <p className="text-sm text-gray-600 mt-1">{item.work_description}</p>
                  )}
                  {item.value_sar && (
                    <p className="text-sm text-gray-500 mt-1">
                      Value: SAR {parseFloat(item.value_sar).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  )}
                </div>
                {!isLocked && (
                  <button
                    onClick={() => handleDelete(item.id)}
                    className="text-sm text-red-600 hover:text-red-800 ml-4"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}