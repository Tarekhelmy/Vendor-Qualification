import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { form4API } from '../../api/client';
import { useConfirm } from '../../hooks/useConfirm';

export default function Form4() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const { confirm, ConfirmDialog } = useConfirm();
  const [personnel, setPersonnel] = useState([]);
  const [availablePositions, setAvailablePositions] = useState([]);
  const [requiredPositions, setRequiredPositions] = useState([]);
  const [formSubmission, setFormSubmission] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    loadFormData();
  }, [applicationId]);

  const loadFormData = async () => {
    try {
      setIsLoading(true);
      const response = await form4API.getData(applicationId);
      setPersonnel(response.data.personnel);
      setAvailablePositions(response.data.available_positions);
      setRequiredPositions(response.data.required_positions);
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

  const handleAddPersonnel = async () => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const newPersonnel = {
      full_name: 'TBD',
      position: availablePositions[0] || 'Project Manager',
      nationality: '',
      highest_educational_qualification: '',
      experience_with_company: 0,
      experience_on_sec_erb_projects: 0,
      experience_total: 0,
    };

    try {
      setSaveStatus('saving');
      setError('');
      const response = await form4API.createPersonnel(applicationId, newPersonnel);
      setPersonnel([...personnel, response.data]);
      showSaveStatus('saved');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to add personnel';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      setSaveStatus('');
      console.error('Add personnel error:', err.response?.data);
    }
  };

  const handleUpdatePersonnel = useCallback(async (personnelId, field, value) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    // Update local state immediately
    setPersonnel(prev => 
      prev.map(p => p.id === personnelId ? { ...p, [field]: value } : p)
    );

    setSaveStatus('saving');
    
    try {
      const updateData = { [field]: value };
      await form4API.updatePersonnel(personnelId, updateData);
      showSaveStatus('saved');
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save changes';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to save changes');
      setSaveStatus('');
      console.error('Update error:', err.response?.data);
    }
  }, [applicationId, formSubmission]);

  const handleDeletePersonnel = async (personnelId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const confirmed = await confirm({
        title: "Delete Project",
        message: "Are you sure you want to delete this personnel record?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
      if (!confirmed) return;
    try {
      await form4API.deletePersonnel(personnelId);
      setPersonnel(personnel.filter(p => p.id !== personnelId));
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete personnel';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete personnel');
    }
  };

  const handleSubmitForm = async () => {
    if (personnel.length === 0) {
      setError('Please add at least one personnel record before submitting');
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
      const response = await form4API.submit(applicationId);
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

  // Calculate position fulfillment
  const positionCounts = personnel.reduce((acc, p) => {
    acc[p.position] = (acc[p.position] || 0) + 1;
    return acc;
  }, {});

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
                Form 4: Total Management and Supervisory Personnel
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

          {/* Required Positions Summary */}
          {requiredPositions.length > 0 && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">Required Positions for This Project:</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {requiredPositions.map(req => {
                  const current = positionCounts[req.position_name] || 0;
                  const isFulfilled = current >= req.minimum_count;
                  return (
                    <div key={req.id} className="flex items-center justify-between text-sm">
                      <span className={isFulfilled ? 'text-green-700' : 'text-blue-700'}>
                        {req.position_name}
                      </span>
                      <span className={`font-medium ${isFulfilled ? 'text-green-600' : 'text-orange-600'}`}>
                        {current}/{req.minimum_count}
                        {isFulfilled && ' ✓'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Add Personnel Button */}
          {!formSubmission?.is_locked && (
            <div className="mb-6">
              <button
                onClick={handleAddPersonnel}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                + Add Personnel
              </button>
            </div>
          )}

          {/* Personnel Table */}
          {personnel.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No personnel added yet. Click "Add Personnel" to get started.</p>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Full Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Position
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Nationality
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Highest Qualification
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Exp. With Company (Years)
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Exp. On SEC-ERB (Years)
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Total Exp. (Years)
                      </th>
                      {!formSubmission?.is_locked && (
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {personnel.map((person) => (
                      <PersonnelRow
                        key={person.id}
                        person={person}
                        availablePositions={availablePositions}
                        isLocked={formSubmission?.is_locked}
                        onUpdate={handleUpdatePersonnel}
                        onDelete={handleDeletePersonnel}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Submit Button */}
          {!formSubmission?.is_locked && personnel.length > 0 && (
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

// Personnel Row Component
function PersonnelRow({ person, availablePositions, isLocked, onUpdate, onDelete }) {
  const [showCustomPosition, setShowCustomPosition] = useState(false);
  const [customPosition, setCustomPosition] = useState('');

  const handleFieldChange = (field, value) => {
    onUpdate(person.id, field, value);
  };

  const handlePositionChange = (value) => {
    if (value === '__custom__') {
      setShowCustomPosition(true);
    } else {
      handleFieldChange('position', value);
      setShowCustomPosition(false);
    }
  };

  const handleCustomPositionSave = () => {
    if (customPosition.trim()) {
      handleFieldChange('position', customPosition.trim());
      setShowCustomPosition(false);
      setCustomPosition('');
    }
  };

  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="text"
          value={person.full_name || ''}
          onChange={(e) => handleFieldChange('full_name', e.target.value)}
          disabled={isLocked}
          className="w-full min-w-[150px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        {showCustomPosition ? (
          <div className="flex items-center space-x-1">
            <input
              type="text"
              value={customPosition}
              onChange={(e) => setCustomPosition(e.target.value)}
              placeholder="Enter position"
              className="w-full min-w-[120px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={handleCustomPositionSave}
              className="px-2 py-1 text-xs text-white bg-green-600 rounded hover:bg-green-700"
            >
              ✓
            </button>
            <button
              onClick={() => {
                setShowCustomPosition(false);
                setCustomPosition('');
              }}
              className="px-2 py-1 text-xs text-gray-600 bg-gray-200 rounded hover:bg-gray-300"
            >
              ✗
            </button>
          </div>
        ) : (
          <select
            value={availablePositions.includes(person.position) ? person.position : '__custom__'}
            onChange={(e) => handlePositionChange(e.target.value)}
            disabled={isLocked}
            className="w-full min-w-[150px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
          >
            {availablePositions.includes(person.position) ? null : (
              <option value="__custom__">{person.position}</option>
            )}
            {availablePositions.map(pos => (
              <option key={pos} value={pos}>{pos}</option>
            ))}
            <option value="__custom__">+ Custom Position...</option>
          </select>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="text"
          value={person.nationality || ''}
          onChange={(e) => handleFieldChange('nationality', e.target.value)}
          disabled={isLocked}
          className="w-full min-w-[100px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="text"
          value={person.highest_educational_qualification || ''}
          onChange={(e) => handleFieldChange('highest_educational_qualification', e.target.value)}
          disabled={isLocked}
          placeholder="e.g., B.Sc."
          className="w-full min-w-[100px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-center">
        <input
          type="number"
          min="0"
          value={person.experience_with_company || 0}
          onChange={(e) => handleFieldChange('experience_with_company', parseInt(e.target.value) || 0)}
          disabled={isLocked}
          className="w-20 px-2 py-1 text-sm text-center border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-center">
        <input
          type="number"
          min="0"
          value={person.experience_on_sec_erb_projects || 0}
          onChange={(e) => handleFieldChange('experience_on_sec_erb_projects', parseInt(e.target.value) || 0)}
          disabled={isLocked}
          className="w-20 px-2 py-1 text-sm text-center border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-center">
        <input
          type="number"
          min="0"
          value={person.experience_total || 0}
          onChange={(e) => handleFieldChange('experience_total', parseInt(e.target.value) || 0)}
          disabled={isLocked}
          className="w-20 px-2 py-1 text-sm text-center border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      {!isLocked && (
        <td className="px-6 py-4 whitespace-nowrap text-center">
          <button
            onClick={() => onDelete(person.id)}
            className="text-red-600 hover:text-red-800 text-sm"
          >
            Delete
          </button>
        </td>
      )}
    </tr>
  );
}