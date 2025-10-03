import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import useAuthStore from './stores/authStore';
import './index.css'; 

// Pages
import Dashboard from './pages/Dashboard';
import Login from './pages/login';
import ApplicationDetail from './pages/ApplicationDetail';
import Form1 from './pages/forms/Form1';
import Form2 from './pages/forms/Form2';
import Form3 from './pages/forms/Form3';
import Form4 from './pages/forms/Form4';
import Form5 from './pages/forms/Form5';
import Form6 from './pages/forms/Form6';
import Form7 from './pages/forms/Form7';
import Form8 from './pages/forms/Form8';
import Profile from './pages/Profile';






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

        <Route
        path="/application/:applicationId/form/4"
        element={
            <ProtectedRoute>
            <Form4 />
            </ProtectedRoute>
        }
        />
        <Route
        path="/application/:applicationId/form/5"
        element={
            <ProtectedRoute>
            <Form5 />
            </ProtectedRoute>
        }
        />
        <Route
        path="/application/:applicationId/form/6"
        element={
            <ProtectedRoute>
            <Form6 />
            </ProtectedRoute>
        }
        />
        <Route
        path="/application/:applicationId/form/7"
        element={
            <ProtectedRoute>
            <Form7 />
            </ProtectedRoute>
        }
        />

        <Route
        path="/application/:applicationId/form/8"
        element={
            <ProtectedRoute>
            <Form8 />
            </ProtectedRoute>
        }
        />

        <Route
        path="/profile"
        element={
            <ProtectedRoute>
            <Profile />
            </ProtectedRoute>
        }
        />

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;