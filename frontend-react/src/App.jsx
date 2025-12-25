/**
 * Mathvidya React App
 * Main application component with routing
 */

import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Layouts
import Layout from './components/common/Layout';

// Auth Pages
import Login from './pages/auth/Login';

// Student Pages
import StudentDashboard from './pages/student/Dashboard';
import TakeExam from './pages/student/TakeExam';

// Teacher Pages
import TeacherQuestions from './pages/teacher/Questions';

// Protected Route Wrapper
const ProtectedRoute = ({ allowedRoles = [] }) => {
  const { user, loading } = useAuth();

  console.log('ProtectedRoute - user:', user, 'loading:', loading, 'allowedRoles:', allowedRoles);

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '100vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  if (!user) {
    console.log('ProtectedRoute - No user, redirecting to login');
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    console.log('ProtectedRoute - Role mismatch, user role:', user.role);
    // Redirect to appropriate dashboard based on role
    const dashboardRoutes = {
      student: '/student/dashboard',
      teacher: '/teacher/questions',
      admin: '/admin/dashboard',
    };
    return <Navigate to={dashboardRoutes[user.role] || '/login'} replace />;
  }

  console.log('ProtectedRoute - Access granted, rendering Outlet');
  return <Outlet />;
};

// Public Route (redirects authenticated users)
const PublicRoute = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center" style={{ minHeight: '100vh' }}>
        <div className="spinner"></div>
      </div>
    );
  }

  if (user) {
    const dashboardRoutes = {
      student: '/student/dashboard',
      teacher: '/teacher/questions',
      admin: '/admin/dashboard',
    };
    return <Navigate to={dashboardRoutes[user.role] || '/student/dashboard'} replace />;
  }

  return <Outlet />;
};

// Teacher Dashboard Placeholder
const TeacherDashboard = () => (
  <div style={{ padding: '2rem' }}>
    <h1>Teacher Dashboard</h1>
    <p className="text-gray mt-3">Coming soon. Use the navigation to access Question Management.</p>
  </div>
);

// Admin Dashboard Placeholder
const AdminDashboard = () => (
  <div style={{ padding: '2rem' }}>
    <h1>Admin Dashboard</h1>
    <p className="text-gray mt-3">Admin functionality coming soon.</p>
  </div>
);

function AppRoutes() {
  return (
    <Routes>
      {/* Public Routes */}
      <Route element={<PublicRoute />}>
        <Route path="/login" element={<Login />} />
      </Route>

      {/* Student Routes */}
      <Route element={<ProtectedRoute allowedRoles={['student']} />}>
        <Route element={<Layout />}>
          <Route path="/student/dashboard" element={<StudentDashboard />} />
        </Route>
        {/* Take Exam - Full screen without Layout */}
        <Route path="/student/take-exam" element={<TakeExam />} />
      </Route>

      {/* Teacher Routes */}
      <Route element={<ProtectedRoute allowedRoles={['teacher']} />}>
        <Route element={<Layout />}>
          <Route path="/teacher/dashboard" element={<TeacherDashboard />} />
          <Route path="/teacher/questions" element={<TeacherQuestions />} />
        </Route>
      </Route>

      {/* Admin Routes */}
      <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route element={<Layout />}>
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
        </Route>
      </Route>

      {/* Default Redirects */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#fff',
              color: '#1F2937',
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
              borderRadius: '0.75rem',
              padding: '1rem 1.5rem',
            },
            success: {
              iconTheme: {
                primary: '#10B981',
                secondary: '#fff',
              },
            },
            error: {
              iconTheme: {
                primary: '#EF4444',
                secondary: '#fff',
              },
            },
          }}
        />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
