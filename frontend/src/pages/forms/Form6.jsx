import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { form6API } from '../../api/client';
import { useConfirm } from '../../hooks/useConfirm';

export default function Form6() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const { confirm, ConfirmDialog } = useConfirm();
  const [manpower, setManpower] = useState([]);
  const [availableCrafts, setAvailableCrafts] = useState([]);
  const [requiredCrafts, setRequiredCrafts] = useState([]);
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
      const response = await form6API.getData(applicationId);
      setManpower(response.data.manpower);
      setAvailableCrafts(response.data.available_crafts);
      setRequiredCrafts(response.data.required_crafts);
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

  const handleAddManpower = async () => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const newManpower = {
      craft_name: availableCrafts[0] || 'General Worker',
      nationality: '',
      quantity: 0,
    };

    try {
      setSaveStatus('saving');
      setError('');
      const response = await form6API.createManpower(applicationId, newManpower);
      setManpower([...manpower, response.data]);
      showSaveStatus('saved');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to add manpower';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      setSaveStatus('');
      console.error('Add manpower error:', err.response?.data);
    }
  };

  const handleUpdateManpower = useCallback(async (manpowerId, field, value) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    // Update local state immediately
    setManpower(prev => 
      prev.map(m => m.id === manpowerId ? { ...m, [field]: value } : m)
    );

    setSaveStatus('saving');
    
    try {
      const updateData = { [field]: value };
      await form6API.updateManpower(manpowerId, updateData);
      showSaveStatus('saved');
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save changes';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to save changes');
      setSaveStatus('');
      console.error('Update error:', err.response?.data);
    }
  }, [applicationId, formSubmission]);

  const handleDeleteManpower = async (manpowerId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const confirmed = await confirm({
        title: "Delete Project",
        message: "Are you sure you want to delete this manpower entry?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;

    try {
      await form6API.deleteManpower(manpowerId);
      setManpower(manpower.filter(m => m.id !== manpowerId));
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete manpower';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete manpower');
    }
  };

  const handleSubmitForm = async () => {
    if (manpower.length === 0) {
      setError('Please add at least one manpower entry before submitting');
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
      const response = await form6API.submit(applicationId);
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

  // Calculate craft fulfillment
  const craftCounts = manpower.reduce((acc, m) => {
    acc[m.craft_name] = (acc[m.craft_name] || 0) + m.quantity;
    return acc;
  }, {});

  // Calculate total manpower
  const totalManpower = manpower.reduce((sum, m) => sum + (m.quantity || 0), 0);

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
                Form 6: Total Skilled and Unskilled Manpower
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

          {/* Summary Card */}
          <div className="mb-6 bg-white shadow rounded-lg p-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="text-sm text-gray-500">Total Manpower Entries</p>
                <p className="text-2xl font-bold text-gray-900">{manpower.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Quantity</p>
                <p className="text-2xl font-bold text-blue-600">{totalManpower}</p>
              </div>
            </div>
          </div>

          {/* Required Crafts Summary */}
          {requiredCrafts.length > 0 && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">Required Crafts for This Project:</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {requiredCrafts.map(req => {
                  const current = craftCounts[req.craft_name] || 0;
                  const isFulfilled = current >= req.minimum_quantity;
                  return (
                    <div key={req.id} className="flex items-center justify-between text-sm">
                      <span className={isFulfilled ? 'text-green-700' : 'text-blue-700'}>
                        {req.craft_name}
                      </span>
                      <span className={`font-medium ${isFulfilled ? 'text-green-600' : 'text-orange-600'}`}>
                        {current}/{req.minimum_quantity}
                        {isFulfilled && ' ✓'}
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Add Manpower Button */}
          {!formSubmission?.is_locked && (
            <div className="mb-6">
              <button
                onClick={handleAddManpower}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                + Add Manpower Entry
              </button>
            </div>
          )}

          {/* Manpower Table */}
          {manpower.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No manpower entries added yet. Click "Add Manpower Entry" to get started.</p>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Craft Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Nationality
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      {!formSubmission?.is_locked && (
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {manpower.map((entry) => (
                      <ManpowerRow
                        key={entry.id}
                        entry={entry}
                        availableCrafts={availableCrafts}
                        isLocked={formSubmission?.is_locked}
                        onUpdate={handleUpdateManpower}
                        onDelete={handleDeleteManpower}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Submit Button */}
          {!formSubmission?.is_locked && manpower.length > 0 && (
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

// Manpower Row Component
function ManpowerRow({ entry, availableCrafts, isLocked, onUpdate, onDelete }) {
  const [showCustomCraft, setShowCustomCraft] = useState(false);
  const [customCraft, setCustomCraft] = useState('');

  const handleFieldChange = (field, value) => {
    onUpdate(entry.id, field, value);
  };

  const handleCraftChange = (value) => {
    if (value === '__custom__') {
      setShowCustomCraft(true);
    } else {
      handleFieldChange('craft_name', value);
      setShowCustomCraft(false);
    }
  };

  const handleCustomCraftSave = () => {
    if (customCraft.trim()) {
      handleFieldChange('craft_name', customCraft.trim());
      setShowCustomCraft(false);
      setCustomCraft('');
    }
  };

  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap">
        {showCustomCraft ? (
          <div className="flex items-center space-x-1">
            <input
              type="text"
              value={customCraft}
              onChange={(e) => setCustomCraft(e.target.value)}
              placeholder="Enter craft name"
              className="w-full min-w-[200px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={handleCustomCraftSave}
              className="px-2 py-1 text-xs text-white bg-green-600 rounded hover:bg-green-700"
            >
              ✓
            </button>
            <button
              onClick={() => {
                setShowCustomCraft(false);
                setCustomCraft('');
              }}
              className="px-2 py-1 text-xs text-gray-600 bg-gray-200 rounded hover:bg-gray-300"
            >
              ✗
            </button>
          </div>
        ) : (
          <select
            value={availableCrafts.includes(entry.craft_name) ? entry.craft_name : '__custom__'}
            onChange={(e) => handleCraftChange(e.target.value)}
            disabled={isLocked}
            className="w-full min-w-[200px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
          >
            {availableCrafts.includes(entry.craft_name) ? null : (
              <option value="__custom__">{entry.craft_name}</option>
            )}
            {availableCrafts.map(craft => (
              <option key={craft} value={craft}>{craft}</option>
            ))}
            <option value="__custom__">+ Custom Craft...</option>
          </select>
        )}
      </td>
      <td className="px-6 py-4">
        <input
          type="text"
          value={entry.nationality || ''}
          onChange={(e) => handleFieldChange('nationality', e.target.value)}
          disabled={isLocked}
          placeholder="e.g., Egyptian, Indian, Saudi"
          className="w-full min-w-[200px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 text-center">
        <input
          type="number"
          min="0"
          value={entry.quantity || 0}
          onChange={(e) => handleFieldChange('quantity', parseInt(e.target.value) || 0)}
          disabled={isLocked}
          className="w-24 px-2 py-1 text-sm text-center border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      {!isLocked && (
        <td className="px-6 py-4 text-center">
          <button
            onClick={() => onDelete(entry.id)}
            className="text-red-600 hover:text-red-800 text-sm"
          >
            Delete
          </button>
        </td>
      )}
    </tr>
  );
}