import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { notificationsAPI } from '../api/client';

export default function PageNotifications({ formNumber = null }) {
  const { applicationId } = useParams();
  const [notifications, setNotifications] = useState([]);
  const [dismissedIds, setDismissedIds] = useState([]);

  useEffect(() => {
    if (applicationId) {
      loadPageNotifications();
    }
  }, [applicationId, formNumber]);

  const loadPageNotifications = async () => {
    try {
      const response = await notificationsAPI.getAll(true, 50); // Get unread only
      
      // Filter notifications relevant to this page
      const filtered = response.data.filter(n => {
        if (n.application_id !== applicationId) return false;
        if (formNumber !== null && n.form_number !== null && n.form_number !== formNumber) return false;
        return !dismissedIds.includes(n.id);
      });

      setNotifications(filtered);
    } catch (err) {
      console.error('Failed to load page notifications:', err);
    }
  };

  const handleDismiss = async (notificationId) => {
    try {
      await notificationsAPI.markAsRead(notificationId);
      setDismissedIds(prev => [...prev, notificationId]);
      setNotifications(prev => prev.filter(n => n.id !== notificationId));
    } catch (err) {
      console.error('Failed to dismiss notification:', err);
    }
  };

  if (notifications.length === 0) return null;

  const getPriorityStyles = (priority) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-50 border-red-300 text-red-900';
      case 'high':
        return 'bg-orange-50 border-orange-300 text-orange-900';
      case 'normal':
        return 'bg-blue-50 border-blue-300 text-blue-900';
      default:
        return 'bg-gray-50 border-gray-300 text-gray-900';
    }
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'document_missing': return '📄';
      case 'document_expired': return '⏰';
      case 'form_incomplete': return '📋';
      case 'feedback': return '💬';
      case 'status_change': return '🔄';
      default: return '🔔';
    }
  };

  return (
    <div className="space-y-3 mb-6">
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`rounded-lg border-l-4 p-4 ${getPriorityStyles(notification.priority)}`}
        >
          <div className="flex items-start">
            <div className="flex-shrink-0 text-2xl mr-3">
              {getTypeIcon(notification.notification_type)}
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-semibold mb-1">
                {notification.title}
              </h3>
              <p className="text-sm whitespace-pre-line">
                {notification.message}
              </p>
              <p className="text-xs mt-2 opacity-75">
                {new Date(notification.created_at).toLocaleString()}
              </p>
            </div>
            <button
              onClick={() => handleDismiss(notification.id)}
              className="flex-shrink-0 ml-4 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}