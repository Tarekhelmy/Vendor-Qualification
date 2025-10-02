import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './stores/authStore';

// Pages
import Dashboard from './pages/Dashboard';
import Login from './pages/login';
import ApplicationDetail from './pages/ApplicationDetail';
import Form1 from './pages/forms/Form1';
import Form2 from './pages/forms/Form2';
import Form3 from './pages/forms/Form3';




// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  const checkAuth = useAuthStore((state) => state.checkAuth);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/application/:applicationId"
          element={
            <ProtectedRoute>
              <ApplicationDetail />
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/application/:applicationId/form/1"
          element={
            <ProtectedRoute>
              <Form1 />
            </ProtectedRoute>
          }
        />

        <Route
        path="/application/:applicationId/form/2"
        element={
            <ProtectedRoute>
            <Form2 />
            </ProtectedRoute>
        }
        />

        <Route
        path="/application/:applicationId/form/3"
        element={
            <ProtectedRoute>
            <Form3 />
            </ProtectedRoute>
        }
        />
        
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;