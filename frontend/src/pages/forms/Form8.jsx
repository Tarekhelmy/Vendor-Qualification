import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { form8API } from '../../api/client';
import { useConfirm } from '../../hooks/useConfirm';
import PageNotifications from '../../components/PageNotifications';

export default function Form8() {
  const { applicationId } = useParams();
  const navigate = useNavigate();
  const { confirm, ConfirmDialog } = useConfirm();
  const [questions, setQuestions] = useState([]);
  const [responses, setResponses] = useState([]);
  const [formSubmission, setFormSubmission] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState('');
  const [error, setError] = useState('');
  const [uploadingFiles, setUploadingFiles] = useState({});

  useEffect(() => {
    loadFormData();
  }, [applicationId]);

  const loadFormData = async () => {
    try {
      setIsLoading(true);
      const response = await form8API.getData(applicationId);
      setQuestions(response.data.questions);
      setResponses(response.data.responses);
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

  const handleAnswerChange = async (questionId, answerText) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Request unlock permission to edit.');
      return;
    }

    // 1. Update local state immediately (This is good)
    setResponses(prev => {
      const existing = prev.find(r => r.question_id === questionId);
      if (existing) {
        // Update existing response
        return prev.map(r => r.question_id === questionId ? { ...r, answer_text: answerText } : r);
      } else {
        // Create a new temporary response object
        return [...prev, { question_id: questionId, answer_text: answerText, attachments: [] }];
      }
    });

    setSaveStatus('saving');

    try {
      // 2. Perform the API call to save the answer
      const result = await form8API.createResponse(applicationId, { question_id: questionId, answer_text: answerText });
      
      // 3. Update the response ID for a newly created response (if needed)
      //    This is more efficient than a full reload if the API returns the new object.
      setResponses(prev => {
        const isNewResponse = !responses.find(r => r.question_id === questionId);
        if (isNewResponse && result.data.id) {
            return prev.map(r => 
                r.question_id === questionId && !r.id 
                ? { ...r, id: result.data.id } 
                : r
            );
        }
        return prev;
      });

      showSaveStatus('saved');
      setError('');
      
      // REMOVED: await loadFormData(); // <--- THIS LINE CAUSED THE JUMP
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to save answer';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to save answer');
      setSaveStatus('');
      console.error('Save error:', err.response?.data);
    }
  };

  const handleFileUpload = async (questionId, file) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Cannot upload files.');
      return;
    }

    const response = responses.find(r => r.question_id === questionId);
    if (!response || !response.id) {
      setError('Please answer the question before uploading attachments');
      return;
    }

    const uploadKey = `${questionId}`;
    setUploadingFiles(prev => ({ ...prev, [uploadKey]: true }));

    try {
      await form8API.uploadAttachment(response.id, file);
      await loadFormData();
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to upload file';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to upload file');
    } finally {
      setUploadingFiles(prev => ({ ...prev, [uploadKey]: false }));
    }
  };

  const handleDeleteAttachment = async (attachmentId) => {
    if (formSubmission?.is_locked) {
      setError('Form is locked. Cannot delete files.');
      return;
    }

    const confirmed = await confirm({
        title: "Delete Project",
        message: "Are you sure you want to delete this file?",
        confirmText: "Delete",
        cancelText: "Cancel",
        type: "danger"
      });
    if (!confirmed) return;

    try {
      await form8API.deleteAttachment(attachmentId);
      await loadFormData();
      setError('');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to delete file';
      setError(typeof errorMsg === 'string' ? errorMsg : 'Failed to delete file');
    }
  };

  const handleSubmitForm = async () => {
    // Only check if all questions are answered
    const unansweredQuestions = questions.filter(q => 
      !responses.find(r => r.question_id === q.id)
    );
  
    if (unansweredQuestions.length > 0) {
      setError(`Please answer all questions. ${unansweredQuestions.length} question(s) remaining.`);
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
      const response = await form8API.submit(applicationId);
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

  const answeredCount = responses.length;
  const totalCount = questions.length;
  const progressPercent = totalCount > 0 ? Math.round((answeredCount / totalCount) * 100) : 0;

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
                Form 8: Project-Specific Questionnaire
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
      <div className="max-w-5xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 sm:px-0">
          {error && (
            <div className="mb-4 rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}
          <PageNotifications formNumber={1} />

          {/* Progress Card */}
          <div className="mb-6 bg-white shadow rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium text-gray-700">Progress</p>
              <p className="text-sm text-gray-600">{answeredCount} / {totalCount} Questions</p>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercent}%` }}
              ></div>
            </div>
          </div>

          {/* Questions List */}
          {questions.length === 0 ? (
            <div className="text-center py-12 bg-white rounded-lg shadow">
              <p className="text-gray-500">No questions available for this project.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {questions.map((question) => {
                const response = responses.find(r => r.question_id === question.id);
                return (
                  <QuestionCard
                    key={question.id}
                    question={question}
                    response={response}
                    isLocked={formSubmission?.is_locked}
                    isUploading={uploadingFiles[question.id]}
                    onAnswerChange={handleAnswerChange}
                    onFileUpload={handleFileUpload}
                    onDeleteAttachment={handleDeleteAttachment}
                  />
                );
              })}
            </div>
          )}

          {/* Submit Button */}
          {!formSubmission?.is_locked && questions.length > 0 && (
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

/// Question Card Component
function QuestionCard({ question, response, isLocked, isUploading, onAnswerChange, onFileUpload, onDeleteAttachment }) {
    const [answer, setAnswer] = useState(response?.answer_text || '');
  
    useEffect(() => {
      setAnswer(response?.answer_text || '');
    }, [response]);
  
    const handleAnswerBlur = () => {
      if (answer !== (response?.answer_text || '')) {
        onAnswerChange(question.id, answer);
      }
    };
  
    const handleFileSelect = (e) => {
      const file = e.target.files[0];
      if (file) {
        onFileUpload(question.id, file);
        e.target.value = '';
      }
    };
  
    const hasAnswer = response && response.answer_text;
    const hasAttachments = response && response.attachments && response.attachments.length > 0;
  
    return (
      <div className="bg-white shadow rounded-lg p-6">
        {/* Question Header */}
        <div className="flex items-start mb-4">
          <span className="flex-shrink-0 inline-flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 text-blue-600 font-semibold text-sm mr-3">
            {question.question_number}
          </span>
          <div className="flex-1">
            <p className="text-sm text-gray-900 leading-relaxed whitespace-pre-line">
              {question.question_text}
            </p>
            {/* REMOVED: {question.requires_attachment && ( ... )} */}
          </div>
          {hasAnswer && (
            <span className="ml-2 text-green-600 text-sm">✓</span>
          )}
        </div>
  
        {/* Answer Input */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">Your Answer</label>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            onBlur={handleAnswerBlur}
            disabled={isLocked}
            rows={4}
            placeholder="Enter your answer here..."
            className="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm disabled:bg-gray-100"
          />
        </div>
  
        {/* Attachments Section - Now always rendered */}
        <div className="border-t pt-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Attachments (Optional)
            {/* REMOVED: {question.requires_attachment && <span className="text-red-500">*</span>} */}
          </label>
          
          {!isLocked && (
            <div className="mb-3">
              <label className="cursor-pointer inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50">
                {isUploading ? 'Uploading...' : 'Upload File'}
                <input
                  type="file"
                  onChange={handleFileSelect}
                  disabled={isUploading || isLocked}
                  className="hidden"
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.xlsx,.xls"
                />
              </label>
              <p className="mt-1 text-xs text-gray-500">
                Supported formats: PDF, DOC, DOCX, JPG, PNG, XLSX (Max 100MB)
              </p>
            </div>
          )}
  
          {hasAttachments ? (
            <ul className="space-y-2">
              {response.attachments.map((attachment) => (
                <li key={attachment.id} className="flex items-center justify-between p-3 bg-gray-50 rounded border border-gray-200">
                  <div className="flex items-center flex-1 min-w-0">
                    <svg className="h-5 w-5 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                    </svg>
                    <span className="text-sm text-gray-700 truncate">{attachment.file_name}</span>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    <a
                      href={attachment.s3_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:text-blue-800"
                    >
                      View
                    </a>
                    {!isLocked && (
                      <button
                        onClick={() => onDeleteAttachment(attachment.id)}
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
            <p className="text-sm text-gray-500 italic">No attachments uploaded</p>
          )}
        </div>
      </div>
    );
  }