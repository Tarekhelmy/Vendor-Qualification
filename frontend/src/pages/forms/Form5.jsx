import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { form5API } from '../../api/client';
import { useConfirm } from '../../hooks/useConfirm';

export default function Form5() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const { confirm, ConfirmDialog } = useConfirm();
  const [personnelList, setPersonnelList] = useState([]);
  const [resumes, setResumes] = useState([]);
  const [formSubmission, setFormSubmission] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');
  const [error, setError] = useState('');
  const [expandedResumes, setExpandedResumes] = useState(new Set());

  useEffect(() => {
    loadFormData();
  }, [applicationId]);

  const loadFormData = async () => {
    try {
      setIsLoading(true);
      const response = await form5API.getData(applicationId);
      setPersonnelList(response.data.personnel_list);
      setResumes(response.data.resumes);
      setFormSubmission(response.data.form_submission);
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load form data';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const showSaveStatus = (status) => {
    setSaveStatus(status);
    if (status === 'saved') {
      setTimeout(() => setSaveStatus(''), 2000);
    }
  };

  const handleCreateResume = async (personnelId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const newResume = {
      personnel_id: personnelId,
      date_of_birth: null,
      additional_notes: '',
    };

    try {
      setSaveStatus('saving');
      setError('');
      const response = await form5API.createResume(applicationId, newResume);
      setResumes([...resumes, response.data]);
      
      // Update personnel list
      setPersonnelList(prev =>
        prev.map(p => p.id === personnelId ? { ...p, has_resume: true, resume_id: response.data.id } : p)
      );
      
      // Auto-expand the newly created resume
      setExpandedResumes(prev => new Set(prev).add(response.data.id));
      
      showSaveStatus('saved');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to create resume';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      setSaveStatus('');
      console.error('Create resume error:', err.response?.data);
    }
  };

  const handleUpdateResume = useCallback(async (resumeId, field, value) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    // Update local state immediately
    setResumes(prev => 
      prev.map(r => r.id === resumeId ? { ...r, [field]: value } : r)
    );

    setSaveStatus('saving');
    
    try {
      const updateData = { [field]: value };
      await form5API.updateResume(resumeId, updateData);
      showSaveStatus('saved');
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save changes';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to save changes');
      setSaveStatus('');
      console.error('Update error:', err.response?.data);
      // Revert the optimistic update on error
      loadFormData();
    }
  }, [formSubmission]);

  const handleDeleteResume = async (resumeId, personnelId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Are you sure you want to delete this resume?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
      if (!confirmed) return;
    try {
      await form5API.deleteResume(resumeId);
      setResumes(resumes.filter(r => r.id !== resumeId));
      
      // Remove from expanded set
      setExpandedResumes(prev => {
        const next = new Set(prev);
        next.delete(resumeId);
        return next;
      });
      
      // Update personnel list
      setPersonnelList(prev =>
        prev.map(p => p.id === personnelId ? { ...p, has_resume: false, resume_id: null } : p)
      );
      
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete resume';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete resume');
    }
  };

  const handleSubmitForm = async () => {
    if (resumes.length === 0) {
      setError('Please create at least one resume before submitting');
      return;
    }
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Are you sure you want to submit this form? It will be locked after submission.",
        confirmText: "Submit",
        cancelText: "Cancel",
        type: "danger"
      });
      if (!confirmed) return;

    try {
      setIsSaving(true);
      setError('');
      const response = await form5API.submit(applicationId);
      setFormSubmission(response.data);
      alert('Form submitted successfully!');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to submit form';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to submit form');
    } finally {
      setIsSaving(false);
    }
  };

  const toggleExpanded = (resumeId) => {
    setExpandedResumes(prev => {
      const next = new Set(prev);
      if (next.has(resumeId)) {
        next.delete(resumeId);
      } else {
        next.add(resumeId);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const personnelWithoutResumes = personnelList.filter(p => !p.has_resume);

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
                Form 5: Resume of Management and Supervisory Personnel
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
          {personnelList.length === 0 && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                No personnel found. Please complete Form 4 first to add management and supervisory personnel before creating resumes.
              </p>
            </div>
          )}

          {/* Available Personnel to Create Resumes For */}
          {!formSubmission?.is_locked && personnelWithoutResumes.length > 0 && (
            <div className="mb-6 bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Personnel without Resumes (Select to Create)
              </h3>
              <div className="space-y-3">
                {personnelWithoutResumes.map((person) => (
                  <div
                    key={person.id}
                    className="border border-gray-200 rounded-lg p-4 hover:border-blue-400 transition"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">
                          {person.full_name}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Position: {person.position} {person.nationality && `| Nationality: ${person.nationality}`}
                        </p>
                      </div>
                      <button
                        onClick={() => handleCreateResume(person.id)}
                        className="ml-4 px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                      >
                        + Create Resume
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Resumes List */}
          {resumes.length === 0 && personnelList.length > 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No resumes created yet. Select personnel above to create resumes.</p>
            </div>
          ) : resumes.length === 0 ? null : (
            <div className="space-y-6">
              {resumes.map((resume) => {
                const person = personnelList.find(p => p.id === resume.personnel_id);
                return (
                  <ResumeCard
                    key={resume.id}
                    resume={resume}
                    person={person}
                    isLocked={formSubmission?.is_locked}
                    isExpanded={expandedResumes.has(resume.id)}
                    onToggleExpanded={() => toggleExpanded(resume.id)}
                    onUpdate={handleUpdateResume}
                    onDelete={handleDeleteResume}
                    onRefresh={loadFormData}
                  />
                );
              })}
            </div>
          )}

          {/* Submit Button */}
          {!formSubmission?.is_locked && resumes.length > 0 && (
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

// Resume Card Component
function ResumeCard({ resume, person, isLocked, isExpanded, onToggleExpanded, onUpdate, onDelete, onRefresh }) {
  const handleFieldChange = (field, value) => {
    onUpdate(resume.id, field, value);
  };

  return (
    <div className="bg-white shadow rounded-lg">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-lg font-medium text-gray-900">
              {person?.full_name || 'Resume'}
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Position: {person?.position} {person?.nationality && `| Nationality: ${person.nationality}`}
            </p>
          </div>
          <div className="flex items-center space-x-2">
            {!isLocked && (
              <button
                onClick={() => onDelete(resume.id, resume.personnel_id)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Delete
              </button>
            )}
            <button
              onClick={onToggleExpanded}
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
          {/* Basic Information */}
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-3">Basic Information</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Name</label>
                <input
                  type="text"
                  value={person?.full_name || ''}
                  disabled
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 text-gray-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Date of Birth</label>
                <input
                  type="date"
                  value={resume.date_of_birth || ''}
                  onChange={(e) => handleFieldChange('date_of_birth', e.target.value)}
                  disabled={isLocked}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Nationality</label>
                <input
                  type="text"
                  value={person?.nationality || ''}
                  disabled
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 text-gray-500 sm:text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Position</label>
                <input
                  type="text"
                  value={person?.position || ''}
                  disabled
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm bg-gray-50 text-gray-500 sm:text-sm"
                />
              </div>
            </div>
          </div>

          {/* Educational Qualifications */}
          <EducationList 
            resumeId={resume.id} 
            education={resume.education || []} 
            isLocked={isLocked} 
            onRefresh={onRefresh} 
          />

          {/* Work Experience */}
          <WorkExperienceList 
            resumeId={resume.id} 
            workExperience={resume.work_experience || []} 
            isLocked={isLocked} 
            onRefresh={onRefresh} 
          />

          {/* Additional Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Additional Notes</label>
            <textarea
              value={resume.additional_notes || ''}
              onChange={(e) => handleFieldChange('additional_notes', e.target.value)}
              disabled={isLocked}
              rows={3}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
              placeholder="Any additional information..."
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Education List Component
function EducationList({ resumeId, education, isLocked, onRefresh }) {
  const [isAdding, setIsAdding] = useState(false);
  const [newItem, setNewItem] = useState({
    institution_name: '',
    year_from: '',
    year_to: '',
    qualification: '',
    certificate_degree: ''
  });

  const handleAdd = async () => {
    if (!newItem.institution_name.trim()) {
      alert('Please enter institution name');
      return;
    }

    try {
      const data = {
        institution_name: newItem.institution_name,
        year_from: newItem.year_from ? parseInt(newItem.year_from) : null,
        year_to: newItem.year_to ? parseInt(newItem.year_to) : null,
        qualification: newItem.qualification || null,
        certificate_degree: newItem.certificate_degree || null
      };
      await form5API.addEducation(resumeId, data);
      setNewItem({ institution_name: '', year_from: '', year_to: '', qualification: '', certificate_degree: '' });
      setIsAdding(false);
      onRefresh();
    } catch (err) {
      alert('Failed to add education');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Delete this education entry?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
      if (!confirmed) return;
    try {
      await form5API.deleteEducation(id);
      onRefresh();
    } catch (err) {
      alert('Failed to delete education');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-medium text-gray-900">Educational Qualifications</h4>
        {!isLocked && !isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            + Add Education
          </button>
        )}
      </div>

      {isAdding && (
        <div className="mb-3 p-4 bg-gray-50 rounded border border-gray-200">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
            <input
              type="text"
              placeholder="Institution Name"
              value={newItem.institution_name}
              onChange={(e) => setNewItem({ ...newItem, institution_name: e.target.value })}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <input
              type="text"
              placeholder="Qualification"
              value={newItem.qualification}
              onChange={(e) => setNewItem({ ...newItem, qualification: e.target.value })}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <input
              type="text"
              placeholder="Certificate/Diploma/Degree"
              value={newItem.certificate_degree}
              onChange={(e) => setNewItem({ ...newItem, certificate_degree: e.target.value })}
              className="px-3 py-2 text-sm border border-gray-300 rounded-md"
            />
            <div className="grid grid-cols-2 gap-2">
              <input
                type="number"
                placeholder="Year From"
                value={newItem.year_from}
                onChange={(e) => setNewItem({ ...newItem, year_from: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md"
                min="1950"
                max="2100"
              />
              <input
                type="number"
                placeholder="Year To"
                value={newItem.year_to}
                onChange={(e) => setNewItem({ ...newItem, year_to: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md"
                min="1950"
                max="2100"
              />
            </div>
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
                setNewItem({ institution_name: '', year_from: '', year_to: '', qualification: '', certificate_degree: '' });
              }}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {education.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No education added</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Institution</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Year From</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Year To</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Qualification</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Certificate/Degree</th>
                {!isLocked && <th className="px-3 py-2"></th>}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {education.map(item => (
                <tr key={item.id}>
                  <td className="px-3 py-2 text-sm text-gray-900">{item.institution_name}</td>
                  <td className="px-3 py-2 text-sm text-gray-500">{item.year_from || '-'}</td>
                  <td className="px-3 py-2 text-sm text-gray-500">{item.year_to || '-'}</td>
                  <td className="px-3 py-2 text-sm text-gray-500">{item.qualification || '-'}</td>
                  <td className="px-3 py-2 text-sm text-gray-500">{item.certificate_degree || '-'}</td>
                  {!isLocked && (
                    <td className="px-3 py-2 text-sm">
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// Work Experience List Component
function WorkExperienceList({ resumeId, workExperience, isLocked, onRefresh }) {
  const [isAdding, setIsAdding] = useState(false);
  const [newItem, setNewItem] = useState({
    company_name: '',
    position: '',
    date_from: '',
    date_to: '',
    is_current: false,
    job_description: ''
  });

  const handleAdd = async () => {
    if (!newItem.company_name.trim() || !newItem.position.trim()) {
      alert('Please enter company name and position');
      return;
    }

    try {
      const data = {
        company_name: newItem.company_name,
        position: newItem.position,
        date_from: newItem.date_from || null,
        date_to: newItem.is_current ? null : (newItem.date_to || null),
        is_current: newItem.is_current,
        job_description: newItem.job_description || null
      };
      await form5API.addWorkExperience(resumeId, data);
      setNewItem({ company_name: '', position: '', date_from: '', date_to: '', is_current: false, job_description: '' });
      setIsAdding(false);
      onRefresh();
    } catch (err) {
      alert('Failed to add work experience');
    }
  };

  const handleDelete = async (id) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: "Delete this work experience?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
      if (!confirmed) return;
    try {
      await form5API.deleteWorkExperience(id);
      onRefresh();
    } catch (err) {
      alert('Failed to delete work experience');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h4 className="text-sm font-medium text-gray-900">Work Experience</h4>
        {!isLocked && !isAdding && (
          <button
            onClick={() => setIsAdding(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            + Add Experience
          </button>
        )}
      </div>

      {isAdding && (
        <div className="mb-3 p-4 bg-gray-50 rounded border border-gray-200">
          <div className="space-y-3 mb-3">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <input
                type="text"
                placeholder="Company Name"
                value={newItem.company_name}
                onChange={(e) => setNewItem({ ...newItem, company_name: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md"
              />
              <input
                type="text"
                placeholder="Position"
                value={newItem.position}
                onChange={(e) => setNewItem({ ...newItem, position: e.target.value })}
                className="px-3 py-2 text-sm border border-gray-300 rounded-md"
              />
              <input
                type="date"
                placeholder="From Date"
                value={newItem.date_from}
                onChange={(e) => setNewItem({ ...newItem, date_from: e.target.value })}
                className="px-3 py-2 text-sm border-gray-300 rounded-md"
              />
              <input
                type="date"
                placeholder="To Date"
                value={newItem.date_to}
                onChange={(e) => setNewItem({ ...newItem, date_to: e.target.value })}
                disabled={newItem.is_current}
                className="px-3 py-2 text-sm border-gray-300 rounded-md disabled:bg-gray-100"
              />
            </div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={newItem.is_current}
                onChange={(e) => setNewItem({ ...newItem, is_current: e.target.checked, date_to: '' })}
                className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
              />
              <span className="ml-2 text-sm text-gray-700">Current Position</span>
            </label>
            <textarea
              placeholder="Brief Job Description"
              value={newItem.job_description}
              onChange={(e) => setNewItem({ ...newItem, job_description: e.target.value })}
              rows={3}
              className="w-full px-3 py-2 text-sm border-gray-300 rounded-md"
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
                setNewItem({ company_name: '', position: '', date_from: '', date_to: '', is_current: false, job_description: '' });
              }}
              className="px-3 py-1 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {workExperience.length === 0 ? (
        <p className="text-sm text-gray-500 italic">No work experience added</p>
      ) : (
        <div className="space-y-3">
          {workExperience.map(item => (
            <div key={item.id} className="p-3 bg-gray-50 rounded border border-gray-200">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{item.company_name}</p>
                  <p className="text-sm text-gray-600 mt-1">{item.position}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {item.date_from ? new Date(item.date_from).toLocaleDateString('en-US', { year: 'numeric', month: 'short' }) : '-'} 
                    {' - '}
                    {item.is_current ? 'Present' : (item.date_to ? new Date(item.date_to).toLocaleDateString('en-US', { year: 'numeric', month: 'short' }) : '-')}
                  </p>
                  {item.job_description && (
                    <p className="text-sm text-gray-600 mt-2 whitespace-pre-line">{item.job_description}</p>
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