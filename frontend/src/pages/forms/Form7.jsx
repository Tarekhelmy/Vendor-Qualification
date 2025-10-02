import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { form7API } from '../../api/client';

export default function Form7() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  
  const [equipment, setEquipment] = useState([]);
  const [availableEquipmentTypes, setAvailableEquipmentTypes] = useState([]);
  const [requiredEquipment, setRequiredEquipment] = useState([]);
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
      const response = await form7API.getData(applicationId);
      setEquipment(response.data.equipment);
      setAvailableEquipmentTypes(response.data.available_equipment_types);
      setRequiredEquipment(response.data.required_equipment);
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

  const handleAddEquipment = async () => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    const newEquipment = {
      equipment_type: availableEquipmentTypes[0] || 'Equipment',
      capacity: '',
      year_of_manufacture: '',
      quantity: 0,
      present_location: 'Riyadh',
    };

    try {
      setSaveStatus('saving');
      setError('');
      const response = await form7API.createEquipment(applicationId, newEquipment);
      setEquipment([...equipment, response.data]);
      showSaveStatus('saved');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to add equipment';
      setError(typeof errorMsg === 'string' ? errorMsg : JSON.stringify(errorMsg));
      setSaveStatus('');
      console.error('Add equipment error:', err.response?.data);
    }
  };

  const handleUpdateEquipment = useCallback(async (equipmentId, field, value) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    // Update local state immediately
    setEquipment(prev => 
      prev.map(e => e.id === equipmentId ? { ...e, [field]: value } : e)
    );

    setSaveStatus('saving');
    
    try {
      const updateData = { [field]: value };
      await form7API.updateEquipment(equipmentId, updateData);
      showSaveStatus('saved');
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save changes';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to save changes');
      setSaveStatus('');
      console.error('Update error:', err.response?.data);
    }
  }, [applicationId, formSubmission]);

  const handleDeleteEquipment = async (equipmentId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    if (!confirm('Are you sure you want to delete this equipment entry?')) return;

    try {
      await form7API.deleteEquipment(equipmentId);
      setEquipment(equipment.filter(e => e.id !== equipmentId));
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete equipment';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete equipment');
    }
  };

  const handleSubmitForm = async () => {
    if (equipment.length === 0) {
      setError('Please add at least one equipment entry before submitting');
      return;
    }

    if (!confirm('Are you sure you want to submit this form? It will be locked after submission.')) {
      return;
    }

    try {
      setIsSaving(true);
      setError('');
      const response = await form7API.submit(applicationId);
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

  // Calculate equipment fulfillment
  const equipmentCounts = equipment.reduce((acc, e) => {
    acc[e.equipment_type] = (acc[e.equipment_type] || 0) + e.quantity;
    return acc;
  }, {});

  // Calculate total equipment
  const totalEquipment = equipment.reduce((sum, e) => sum + (e.quantity || 0), 0);

  return (
    <div className="min-h-screen bg-gray-50">
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
                Form 7: List of Equipment and Tools
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
                <p className="text-sm text-gray-500">Total Equipment Entries</p>
                <p className="text-2xl font-bold text-gray-900">{equipment.length}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Total Quantity</p>
                <p className="text-2xl font-bold text-blue-600">{totalEquipment}</p>
              </div>
            </div>
          </div>

          {/* Required Equipment Summary */}
          {requiredEquipment.length > 0 && (
            <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">Required Equipment for This Project:</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {requiredEquipment.map(req => {
                  const current = equipmentCounts[req.equipment_type] || 0;
                  const isFulfilled = current >= req.minimum_quantity;
                  return (
                    <div key={req.id} className="flex items-center justify-between text-sm">
                      <span className={isFulfilled ? 'text-green-700' : 'text-blue-700'}>
                        {req.equipment_type}
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

          {/* Add Equipment Button */}
          {!formSubmission?.is_locked && (
            <div className="mb-6">
              <button
                onClick={handleAddEquipment}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
              >
                + Add Equipment/Tool
              </button>
            </div>
          )}

          {/* Equipment Table */}
          {equipment.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No equipment entries added yet. Click "Add Equipment/Tool" to get started.</p>
            </div>
          ) : (
            <div className="bg-white shadow overflow-hidden sm:rounded-lg">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Capacity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Year of Manufacture
                      </th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantity
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Present Location
                      </th>
                      {!formSubmission?.is_locked && (
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Actions
                        </th>
                      )}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {equipment.map((entry) => (
                      <EquipmentRow
                        key={entry.id}
                        entry={entry}
                        availableEquipmentTypes={availableEquipmentTypes}
                        isLocked={formSubmission?.is_locked}
                        onUpdate={handleUpdateEquipment}
                        onDelete={handleDeleteEquipment}
                      />
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Submit Button */}
          {!formSubmission?.is_locked && equipment.length > 0 && (
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

// Equipment Row Component
function EquipmentRow({ entry, availableEquipmentTypes, isLocked, onUpdate, onDelete }) {
  const [showCustomType, setShowCustomType] = useState(false);
  const [customType, setCustomType] = useState('');

  const handleFieldChange = (field, value) => {
    onUpdate(entry.id, field, value);
  };

  const handleTypeChange = (value) => {
    if (value === '__custom__') {
      setShowCustomType(true);
    } else {
      handleFieldChange('equipment_type', value);
      setShowCustomType(false);
    }
  };

  const handleCustomTypeSave = () => {
    if (customType.trim()) {
      handleFieldChange('equipment_type', customType.trim());
      setShowCustomType(false);
      setCustomType('');
    }
  };

  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap">
        {showCustomType ? (
          <div className="flex items-center space-x-1">
            <input
              type="text"
              value={customType}
              onChange={(e) => setCustomType(e.target.value)}
              placeholder="Enter equipment type"
              className="w-full min-w-[200px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
              autoFocus
            />
            <button
              onClick={handleCustomTypeSave}
              className="px-2 py-1 text-xs text-white bg-green-600 rounded hover:bg-green-700"
            >
              ✓
            </button>
            <button
              onClick={() => {
                setShowCustomType(false);
                setCustomType('');
              }}
              className="px-2 py-1 text-xs text-gray-600 bg-gray-200 rounded hover:bg-gray-300"
            >
              ✗
            </button>
          </div>
        ) : (
          <select
            value={availableEquipmentTypes.includes(entry.equipment_type) ? entry.equipment_type : '__custom__'}
            onChange={(e) => handleTypeChange(e.target.value)}
            disabled={isLocked}
            className="w-full min-w-[200px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
          >
            {availableEquipmentTypes.includes(entry.equipment_type) ? null : (
              <option value="__custom__">{entry.equipment_type}</option>
            )}
            {availableEquipmentTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
            <option value="__custom__">+ Custom Equipment...</option>
          </select>
        )}
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="text"
          value={entry.capacity || ''}
          onChange={(e) => handleFieldChange('capacity', e.target.value)}
          disabled={isLocked}
          placeholder="N/A or specify"
          className="w-full min-w-[120px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="text"
          value={entry.year_of_manufacture || ''}
          onChange={(e) => handleFieldChange('year_of_manufacture', e.target.value)}
          disabled={isLocked}
          placeholder="e.g., 2020 or 2018-2022"
          className="w-full min-w-[120px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-center">
        <input
          type="number"
          min="0"
          value={entry.quantity || 0}
          onChange={(e) => handleFieldChange('quantity', parseInt(e.target.value) || 0)}
          disabled={isLocked}
          className="w-24 px-2 py-1 text-sm text-center border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      <td className="px-6 py-4 whitespace-nowrap">
        <input
          type="text"
          value={entry.present_location || ''}
          onChange={(e) => handleFieldChange('present_location', e.target.value)}
          disabled={isLocked}
          placeholder="Location"
          className="w-full min-w-[120px] px-2 py-1 text-sm border border-gray-300 rounded focus:border-blue-500 focus:ring-1 focus:ring-blue-500 disabled:bg-gray-100"
        />
      </td>
      {!isLocked && (
        <td className="px-6 py-4 whitespace-nowrap text-center">
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