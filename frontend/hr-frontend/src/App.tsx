import type { ReactNode } from 'react';
import { useAuth } from './state/authContext';
import { Routes, Route, Link, Navigate } from 'react-router-dom';
import LoginPage from './pages/auth/login';
import ChatPage from './pages/chat';
import DocumentsPage from './pages/documents';
import DocumentViewerPage from './pages/document-viewer';
import ProfilePage from './pages/profile';
import HomePage from './pages/home';
import AboutPage from './pages/about';
import HRAdminDashboard from './pages/hr-admin-dashboard';
import EmployeeDashboard from './pages/employee-dashboard';
import ChangePasswordPage from './pages/change-password';
import EmployeesPage from './pages/employees';

function RequireAuth({ children, role }: { children: ReactNode; role?: 'hr_admin' | 'employee' }) {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (role && user.role !== role) {
    return <Navigate to="/employee-dashboard" replace />;
  }
  return <>{children}</>;
}

function GuestOnly({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user) {
    return (
      <Navigate
        to={user.role === 'hr_admin' ? '/hr-admin-dashboard' : '/employee-dashboard'}
        replace
      />
    );
  }
  return <>{children}</>;
}

export default function App() {
  const { user, logout, initialized } = useAuth();

  const isLoggedIn = user !== null;

  const navLinks = [
    { path: '/', label: 'Home' },
    { path: '/about', label: 'About' },
  ];

  const employeeLinks = [
    { path: '/employee-dashboard', label: 'Home' },
    { path: '/about', label: 'About' },
    { path: '/documents', label: 'Documents' },
    { path: '/chat', label: 'Chat' },
    { path: '/profile', label: 'Profile' },
    { path: '/change-password', label: 'Change Password' },
  ];

  const hrAdminLinks = [
    { path: '/hr-admin-dashboard', label: 'Home' },
    { path: '/about', label: 'About' },
    { path: '/employees', label: 'Employees' },
    { path: '/documents', label: 'Documents' },
    { path: '/chat', label: 'Chat' },
    { path: '/profile', label: 'Profile' },
    { path: '/change-password', label: 'Change Password' },
  ];

  const getLinks = () => {
    if (!isLoggedIn) return navLinks;
    if (user?.role === 'employee') return employeeLinks;
    if (user?.role === 'hr_admin') return hrAdminLinks;
    return navLinks;
  };

  const links = getLinks();

  if (!initialized) {
    return (
      <div style={{ textAlign: 'center', padding: '3rem', color: '#52525b' }}>
        Loading...
      </div>
    );
  }

  return (
    <div>
      <nav
        style={{
          background: '#2c3e50',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          color: '#fff',
        }}
      >
        <Link to="/" style={{ fontSize: '1.5rem', fontWeight: 600, color: '#fff' }}>
          HR Policy Assistant
        </Link>
        {links.map((link) => (
          <Link
            key={link.path}
            to={link.path}
            style={{
              marginLeft: '1rem',
              color: '#fff',
              textDecoration: 'none',
              fontWeight: 500,
            }}
          >
            {link.label}
          </Link>
        ))}
        {isLoggedIn ? (
          <button
            style={{
              background: 'transparent',
              border: '1px solid #fff',
              color: '#fff',
              padding: '0.5rem 1rem',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
            onClick={logout}
          >
            Logout
          </button>
        ) : (
          <Link
            to="/login"
            style={{ marginLeft: '1rem', color: '#fff', textDecoration: 'none', fontWeight: 500 }}
          >
            Login
          </Link>
        )}
      </nav>

      <hr style={{ borderColor: 'rgba(255,255,255,0.3)', margin: '1rem 0' }} />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/about" element={<AboutPage />} />
        <Route
          path="/login"
          element={
            <GuestOnly>
              <LoginPage />
            </GuestOnly>
          }
        />
        <Route
          path="/chat"
          element={
            <RequireAuth>
              <ChatPage />
            </RequireAuth>
          }
        />
        <Route
          path="/documents"
          element={
            <RequireAuth>
              <DocumentsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/documents/:id/view"
          element={
            <RequireAuth>
              <DocumentViewerPage />
            </RequireAuth>
          }
        />
        <Route
          path="/employees"
          element={
            <RequireAuth role="hr_admin">
              <EmployeesPage />
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <ProfilePage />
            </RequireAuth>
          }
        />
        <Route
          path="/change-password"
          element={
            <RequireAuth>
              <ChangePasswordPage />
            </RequireAuth>
          }
        />
        <Route
          path="/hr-admin-dashboard"
          element={
            <RequireAuth role="hr_admin">
              <HRAdminDashboard />
            </RequireAuth>
          }
        />
        <Route
          path="/employee-dashboard"
          element={
            <RequireAuth>
              <EmployeeDashboard />
            </RequireAuth>
          }
        />
      </Routes>
    </div>
  );
}
