import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { profileAPI } from '../api/client';
import useAuthStore from '../stores/authStore';
import { useConfirm } from '../hooks/useConfirm';

export default function Profile() {
  const navigate = useNavigate();
  const { vendor, logout } = useAuthStore();
  const { confirm, ConfirmDialog } = useConfirm();
  const [profileData, setProfileData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [uploadingFiles, setUploadingFiles] = useState({});

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setIsLoading(true);
      const response = await profileAPI.getProfile();
      setProfileData(response.data);
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load profile';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to load profile');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFinancialUpload = async (year, file) => {
    const uploadKey = `financial_${year}`;
    setUploadingFiles(prev => ({ ...prev, [uploadKey]: true }));

    try {
      await profileAPI.uploadFinancialStatement(year, file);
      await loadProfile();
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to upload financial statement';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to upload financial statement');
    } finally {
      setUploadingFiles(prev => ({ ...prev, [uploadKey]: false }));
    }
  };

  const handleFinancialDelete = async (year) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: `Delete financial statement for ${year}?`,
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;

    try {
      await profileAPI.deleteFinancialStatement(year);
      await loadProfile();
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete financial statement';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete');
    }
  };

  const handleLegalUpload = async (documentType, file) => {
    const uploadKey = `legal_${documentType}`;
    setUploadingFiles(prev => ({ ...prev, [uploadKey]: true }));

    try {
      await profileAPI.uploadLegalDocument(documentType, file);
      await loadProfile();
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to upload legal document';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to upload legal document');
    } finally {
      setUploadingFiles(prev => ({ ...prev, [uploadKey]: false }));
    }
  };

  const handleLegalDelete = async (documentType) => {
    const confirmed = await confirm({
        title: "Delete Project",
        message: `Delete this legal document?`,
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;


    try {
      await profileAPI.deleteLegalDocument(documentType);
      await loadProfile();
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete legal document';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete');
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const currentYear = new Date().getFullYear();
  const requiredYears = Array.from({ length: 5 }, (_, i) => currentYear - 5 + i);
  
  const financialStatementsMap = (profileData?.financial_statements || []).reduce((acc, fs) => {
    acc[fs.year] = fs;
    return acc;
  }, {});

  const legalDocumentsMap = (profileData?.legal_documents || []).reduce((acc, doc) => {
    acc[doc.document_type] = doc;
    return acc;
  }, {});

  const legalDocTypes = [
    { key: 'classification_certificate', label: 'Classification Certificate' },
    { key: 'saudi_contractors_authority', label: 'Saudi Contractors Authority Certificate' },
    { key: 'municipal_registration', label: 'Municipal Registration Certificate' }
  ];

  const isProfileIncomplete = !profileData?.profile_complete;

  return (
    <div className="min-h-screen bg-gray-50">
    {/* This line renders the confirmation modal */}
    <ConfirmDialog />
      {/* Header */}
      <nav className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <button
                onClick={() => navigate('/')}
                className="text-gray-600 hover:text-gray-900 mr-4"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-xl font-bold text-gray-900">Company Profile</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{vendor?.company_name}</span>
              <button
                onClick={logout}
                className="text-sm text-gray-700 hover:text-gray-900"
              >
                Logout
              </button>
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

          {/* Profile Completion Warning */}
          {isProfileIncomplete && (
            <div className="mb-6 rounded-lg bg-orange-50 border-2 border-orange-400 p-4 animate-pulse">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-orange-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-orange-800">
                    Profile Incomplete
                  </h3>
                  <div className="mt-2 text-sm text-orange-700">
                    <p>Please complete your profile by uploading the following:</p>
                    <ul className="list-disc list-inside mt-1">
                      {profileData?.missing_items.map((item, idx) => (
                        <li key={idx}>{item}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Company Information */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Company Information
              </h3>
            </div>
            <div className="border-t border-gray-200 px-4 py-5 sm:px-6">
              <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium text-gray-500">Company Name</dt>
                  <dd className="mt-1 text-sm text-gray-900">{vendor?.company_name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Contact Person</dt>
                  <dd className="mt-1 text-sm text-gray-900">{vendor?.contact_person_name}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Email</dt>
                  <dd className="mt-1 text-sm text-gray-900">{vendor?.contact_person_email}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-500">Phone Number</dt>
                  <dd className="mt-1 text-sm text-gray-900">{vendor?.contact_person_phone}</dd>
                </div>
              </dl>
            </div>
          </div>

          {/* Financial Statements */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg mb-6">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Financial Statements (Last 5 Years)
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Upload financial statements for each of the last 5 years
              </p>
            </div>
            <div className="border-t border-gray-200">
              <ul className="divide-y divide-gray-200">
                {requiredYears.map((year) => {
                  const statement = financialStatementsMap[year];
                  const uploadKey = `financial_${year}`;
                  const isUploading = uploadingFiles[uploadKey];

                  return (
                    <li key={year} className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            Year {year}
                            {!statement && <span className="ml-2 text-red-500">*</span>}
                          </p>
                          {statement && (
                            <p className="text-sm text-gray-500 mt-1">{statement.file_name}</p>
                          )}
                        </div>
                        <div className="ml-4 flex items-center space-x-2">
                          {statement ? (
                            <>
                              <a
                                href={statement.s3_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-blue-600 hover:text-blue-800"
                              >
                                View
                              </a>
                              <button
                                onClick={() => handleFinancialDelete(year)}
                                className="text-sm text-red-600 hover:text-red-800"
                              >
                                Delete
                              </button>
                            </>
                          ) : (
                            <label className="cursor-pointer inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                              {isUploading ? 'Uploading...' : 'Upload'}
                              <input
                                type="file"
                                onChange={(e) => {
                                  const file = e.target.files[0];
                                  if (file) {
                                    handleFinancialUpload(year, file);
                                    e.target.value = '';
                                  }
                                }}
                                disabled={isUploading}
                                className="hidden"
                                accept=".pdf,.xlsx,.xls"
                              />
                            </label>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>

          {/* Legal Documents */}
          <div className="bg-white shadow overflow-hidden sm:rounded-lg">
            <div className="px-4 py-5 sm:px-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Legal Documents
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                Upload all required legal certificates
              </p>
            </div>
            <div className="border-t border-gray-200">
              <ul className="divide-y divide-gray-200">
                {legalDocTypes.map((docType) => {
                  const document = legalDocumentsMap[docType.key];
                  const uploadKey = `legal_${docType.key}`;
                  const isUploading = uploadingFiles[uploadKey];

                  return (
                    <li key={docType.key} className="px-4 py-4 sm:px-6">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {docType.label}
                            {!document && <span className="ml-2 text-red-500">*</span>}
                          </p>
                          {document && (
                            <p className="text-sm text-gray-500 mt-1">{document.file_name}</p>
                          )}
                        </div>
                        <div className="ml-4 flex items-center space-x-2">
                          {document ? (
                            <>
                              <a
                                href={document.s3_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-blue-600 hover:text-blue-800"
                              >
                                View
                              </a>
                              <button
                                onClick={() => handleLegalDelete(docType.key)}
                                className="text-sm text-red-600 hover:text-red-800"
                              >
                                Delete
                              </button>
                            </>
                          ) : (
                            <label className="cursor-pointer inline-flex items-center px-3 py-1 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                              {isUploading ? 'Uploading...' : 'Upload'}
                              <input
                                type="file"
                                onChange={(e) => {
                                  const file = e.target.files[0];
                                  if (file) {
                                    handleLegalUpload(docType.key, file);
                                    e.target.value = '';
                                  }
                                }}
                                disabled={isUploading}
                                className="hidden"
                                accept=".pdf,.jpg,.jpeg,.png"
                              />
                            </label>
                          )}
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </div>
          </div>

          {/* Profile Complete Badge */}
          {profileData?.profile_complete && (
            <div className="mt-6 rounded-md bg-green-50 p-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-green-800">
                    Profile Complete! All required documents have been uploaded.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}