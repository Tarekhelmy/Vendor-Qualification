import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { notificationsAPI } from '../api/client';

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000); // Poll every 30 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (isOpen && notifications.length === 0) {
      loadNotifications();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const loadUnreadCount = async () => {
    try {
      const response = await notificationsAPI.getUnreadCount();
      setUnreadCount(response.data.count);
    } catch (err) {
      console.error('Failed to load unread count:', err);
    }
  };

  const loadNotifications = async () => {
    try {
      setIsLoading(true);
      const response = await notificationsAPI.getAll(false, 20);
      setNotifications(response.data);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Update the handleNotificationClick function:
const handleNotificationClick = async (notification) => {
    if (!notification.is_read) {
      await notificationsAPI.markAsRead(notification.id);
      setUnreadCount(prev => Math.max(0, prev - 1));
      setNotifications(prev =>
        prev.map(n => n.id === notification.id ? { ...n, is_read: true } : n)
      );
    }
  
    // Smart routing based on notification type and action_url
    if (notification.action_url) {
      navigate(notification.action_url);
    } else if (notification.application_id) {
      // Default routing based on form_number
      if (notification.form_number) {
        navigate(`/application/${notification.application_id}/form/${notification.form_number}`);
      } else {
        navigate(`/application/${notification.application_id}`);
      }
    }
    
    setIsOpen(false);
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationsAPI.markAllRead();
      setUnreadCount(0);
      setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 border-red-300';
      case 'high': return 'bg-orange-100 border-orange-300';
      case 'normal': return 'bg-blue-50 border-blue-200';
      default: return 'bg-gray-50 border-gray-200';
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
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-600 rounded-full">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-lg border border-gray-200 z-50">
          {/* Header */}
          <div className="px-4 py-3 border-b border-gray-200 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-gray-900">Notifications</h3>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Mark all read
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="max-h-96 overflow-y-auto">
            {isLoading ? (
              <div className="py-8 text-center text-gray-500">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              </div>
            ) : notifications.length === 0 ? (
              <div className="py-8 text-center text-gray-500">
                <p className="text-sm">No notifications</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {notifications.map((notification) => (
                  <button
                    key={notification.id}
                    onClick={() => handleNotificationClick(notification)}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition ${
                      !notification.is_read ? 'bg-blue-50' : ''
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <span className="text-2xl flex-shrink-0">
                        {getTypeIcon(notification.notification_type)}
                      </span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <p className={`text-sm font-medium text-gray-900 ${
                            !notification.is_read ? 'font-semibold' : ''
                          }`}>
                            {notification.title}
                          </p>
                          {!notification.is_read && (
                            <span className="ml-2 flex-shrink-0 w-2 h-2 bg-blue-600 rounded-full"></span>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-400 mt-1">
                          {new Date(notification.created_at).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                        </p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-3 border-t border-gray-200">
              <button
                onClick={() => {
                  navigate('/notifications');
                  setIsOpen(false);
                }}
                className="text-xs text-blue-600 hover:text-blue-800 font-medium"
              >
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}