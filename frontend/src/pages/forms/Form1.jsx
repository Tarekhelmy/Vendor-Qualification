import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { form1API, documentsAPI } from '../../api/client';
import { useConfirm } from '../../hooks/useConfirm';


export default function Form1() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const { confirm, ConfirmDialog } = useConfirm();
  const [projects, setProjects] = useState([]);
  const [formSubmission, setFormSubmission] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState(''); // 'saving', 'saved', ''
  const [error, setError] = useState('');
  const [uploadingDocs, setUploadingDocs] = useState({});

  useEffect(() => {
    loadFormData();
  }, [applicationId]);

  const loadFormData = async () => {
    try {
      setIsLoading(true);
      const response = await form1API.getData(applicationId);
      setProjects(response.data.projects);
      setFormSubmission(response.data.form_submission);
      setError(''); // Clear any previous errors
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

  const handleAddProject = async () => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const newProject = {
      project_field: 'Similar',
      client_name: 'TBD',  // Changed from '' to 'TBD'
      project_title: 'TBD',  // Changed from '' to 'TBD'
      contract_start_date: '',
      contract_completion_date: '',
    };

    try {
      setSaveStatus('saving');
      setError(''); // Clear previous errors
      const response = await form1API.createProject(applicationId, newProject);
      setProjects([...projects, response.data]);
      showSaveStatus('saved');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to add project';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      setSaveStatus('');
      console.error('Add project error:', err.response?.data);
    }
  };

  const handleUpdateProject = useCallback(async (projectId, field, value) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    // Update local state immediately
    setProjects(prev => 
      prev.map(p => p.id === projectId ? { ...p, [field]: value } : p)
    );

    // Debounced save to backend
    setSaveStatus('saving');
    
    try {
      const updateData = { [field]: value };
      await form1API.updateProject(projectId, updateData);
      showSaveStatus('saved');
      setError(''); // Clear errors on success
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save changes';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to save changes');
      setSaveStatus('');
      console.error('Update error:', err.response?.data);
    }
  }, [applicationId, formSubmission]);

  const handleDeleteProject = async (projectId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }
    const confirmed = await confirm({
      title: "Delete Project",
      message: "Are you sure you want to delete this project? This action cannot be undone.",
      confirmText: "Delete",
      cancelText: "Cancel",
      type: "danger"
    });
    if (!confirmed) return;

    try {
      await form1API.deleteProject(projectId);
      setProjects(projects.filter(p => p.id !== projectId));
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete project';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete project');
    }
  };

  const handleFileUpload = async (projectId, documentType, file) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Cannot upload documents.');
      return;
    }

    const uploadKey = `${projectId}-${documentType}`;
    setUploadingDocs(prev => ({ ...prev, [uploadKey]: true }));

    try {
      const formData = new FormData();
      formData.append('application_id', applicationId);
      formData.append('form_number', '1');
      formData.append('document_type', documentType);
      formData.append('related_entity_id', projectId);
      formData.append('file', file);

      const response = await documentsAPI.upload(formData);
      
      // Update project with new document
      setProjects(prev =>
        prev.map(p => {
          if (p.id === projectId) {
            return {
              ...p,
              documents: [...(p.documents || []), response.data]
            };
          }
          return p;
        })
      );

      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to upload document';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to upload document');
    } finally {
      setUploadingDocs(prev => ({ ...prev, [uploadKey]: false }));
    }
  };

  const handleDeleteDocument = async (projectId, documentId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Cannot delete documents.');
      return;
    }

    const confirmed = await confirm({
      title: "Delete Project",
      message: "Are you sure you want to delete this document?",
      confirmText: "Delete",
      cancelText: "Cancel",
      type: "danger"
    });
    if (!confirmed) return;

    try {
      await documentsAPI.delete(documentId);
      
      setProjects(prev =>
        prev.map(p => {
          if (p.id === projectId) {
            return {
              ...p,
              documents: (p.documents || []).filter(d => d.id !== documentId)
            };
          }
          return p;
        })
      );
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete document';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete document');
    }
  };

  const handleSubmitForm = async () => {
    if (projects.length === 0) {
      setError('Please add at least one completed project before submitting');
      return;
    }

    const confirmed = await confirm({
      title: "Submit Form",
      message: "Are you sure you want to submit this form? It will be locked after submission.",
      confirmText: "Submit",
      cancelText: "Cancel",
      type: "warning"
    });

    if (!confirmed) return;


    try {
      setIsSaving(true);
      setError('');
      const response = await form1API.submit(applicationId);
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
                Form 1: List of Projects Completed (Last 5 Years)
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

          {/* Add Project Button */}
          {!formSubmission?.is_locked && (
            <div className="mb-6">
              <button
                onClick={handleAddProject}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                + Add Project
              </button>
            </div>
          )}

          {/* Projects List */}
          {projects.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No projects added yet. Click "Add Project" to get started.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {projects.map((project, index) => (
                <ProjectCard
                  key={project.id}
                  project={project}
                  index={index}
                  isLocked={formSubmission?.is_locked}
                  onUpdate={handleUpdateProject}
                  onDelete={handleDeleteProject}
                  onFileUpload={handleFileUpload}
                  onDeleteDocument={handleDeleteDocument}
                  uploadingDocs={uploadingDocs}
                />
              ))}
            </div>
          )}

          {/* Submit Button */}
          {!formSubmission?.is_locked && projects.length > 0 && (
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

// Project Card Component
function ProjectCard({ 
  project, 
  index, 
  isLocked, 
  onUpdate, 
  onDelete, 
  onFileUpload, 
  onDeleteDocument,
  uploadingDocs 
}) {
  const handleFieldChange = (field, value) => {
    onUpdate(project.id, field, value);
  };

  const getProjectDocuments = (type) => {
    return (project.documents || []).filter(d => d.document_type === type);
  };

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-medium text-gray-900">Project {index + 1}</h3>
        {!isLocked && (
          <button
            onClick={() => onDelete(project.id)}
            className="text-red-600 hover:text-red-800 text-sm"
          >
            Delete
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Project Field */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Project Field <span className="text-red-500">*</span>
          </label>
          <select
            value={project.project_field || ''}
            onChange={(e) => handleFieldChange('project_field', e.target.value)}
            disabled={isLocked}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          >
            <option value="Similar">Similar</option>
            <option value="Related">Related</option>
            <option value="Other">Other</option>
          </select>
        </div>

        {/* Contract Number */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Contract No.
          </label>
          <input
            type="text"
            value={project.contract_number || ''}
            onChange={(e) => handleFieldChange('contract_number', e.target.value)}
            disabled={isLocked}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Contract Signing Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Contract Signing Date
          </label>
          <input
            type="date"
            value={project.contract_signing_date || ''}
            onChange={(e) => handleFieldChange('contract_signing_date', e.target.value)}
            disabled={isLocked}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Client Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Client Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={project.client_name || ''}
            onChange={(e) => handleFieldChange('client_name', e.target.value)}
            disabled={isLocked}
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Client Representative Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Client's Representative Name
          </label>
          <input
            type="text"
            value={project.client_representative_name || ''}
            onChange={(e) => handleFieldChange('client_representative_name', e.target.value)}
            disabled={isLocked}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Client Phone */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Client's Telephone Number
          </label>
          <input
            type="tel"
            value={project.client_phone || ''}
            onChange={(e) => handleFieldChange('client_phone', e.target.value)}
            disabled={isLocked}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Project Title - Full Width */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Project/Contract Title <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={project.project_title || ''}
            onChange={(e) => handleFieldChange('project_title', e.target.value)}
            disabled={isLocked}
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Project Description - Full Width */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Brief Description of Work
          </label>
          <textarea
            value={project.project_description || ''}
            onChange={(e) => handleFieldChange('project_description', e.target.value)}
            disabled={isLocked}
            rows={3}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Contract Start Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Contract Start Date <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={project.contract_start_date || ''}
            onChange={(e) => handleFieldChange('contract_start_date', e.target.value)}
            disabled={isLocked}
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Contract Completion Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Contract Completion Date <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            value={project.contract_completion_date || ''}
            onChange={(e) => handleFieldChange('contract_completion_date', e.target.value)}
            disabled={isLocked}
            required
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>

        {/* Contract Value */}
        <div className="md:col-span-2">
          <label className="block text-sm font-medium text-gray-700">
            Value (Saudi Riyals)
          </label>
          <input
            type="number"
            step="0.01"
            value={project.contract_value_sar || ''}
            onChange={(e) => handleFieldChange('contract_value_sar', e.target.value)}
            disabled={isLocked}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>
      </div>

      {/* Document Uploads */}
      <div className="mt-6 border-t pt-6">
        <h4 className="text-sm font-medium text-gray-900 mb-4">Required Documents</h4>
        
        <div className="space-y-4">
          {/* Contract Upload */}
          <DocumentUploadSection
            label="Contract"
            documentType="contract"
            projectId={project.id}
            documents={getProjectDocuments('contract')}
            isLocked={isLocked}
            isUploading={uploadingDocs[`${project.id}-contract`]}
            onUpload={onFileUpload}
            onDelete={onDeleteDocument}
          />

          {/* Invoice Upload */}
          <DocumentUploadSection
            label="Invoices"
            documentType="invoice"
            projectId={project.id}
            documents={getProjectDocuments('invoice')}
            isLocked={isLocked}
            isUploading={uploadingDocs[`${project.id}-invoice`]}
            onUpload={onFileUpload}
            onDelete={onDeleteDocument}
          />
        </div>
      </div>
    </div>
  );
}

// Document Upload Section Component
function DocumentUploadSection({ 
  label, 
  documentType, 
  projectId, 
  documents, 
  isLocked, 
  isUploading,
  onUpload, 
  onDelete 
}) {
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      onUpload(projectId, documentType, file);
      e.target.value = ''; // Reset input
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">
        {label}
      </label>
      
      {!isLocked && (
        <div className="mb-2">
          <label className="cursor-pointer inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
            {isUploading ? 'Uploading...' : `Upload ${label}`}
            <input
              type="file"
              onChange={handleFileSelect}
              disabled={isUploading}
              className="hidden"
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            />
          </label>
        </div>
      )}

      {documents.length > 0 ? (
        <ul className="space-y-2">
          {documents.map((doc) => (
            <li key={doc.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-sm text-gray-700">{doc.file_name}</span>
              <div className="flex items-center space-x-2">
                <a
                  href={doc.s3_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  View
                </a>
                {!isLocked && (
                  <button
                    onClick={() => onDelete(projectId, doc.id)}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Delete
                  </button>
                )}
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-gray-500 italic">No {label.toLowerCase()} uploaded</p>
      )}
    </div>
  );
}