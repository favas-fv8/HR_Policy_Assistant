import type { ReactNode } from 'react';
import { useAuth } from './state/authContext';
import { Routes, Route, Link, NavLink, Navigate } from 'react-router-dom';
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
import AppFooter from './components/layout/AppFooter';
import NeuralBackground from './components/layout/NeuralBackground';

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
    <div className="app-shell neural-theme">
      <NeuralBackground />
      <nav className="app-nav">
        <Link to="/" className="app-brand">
          <img src="/images/icon-image.png" alt="" className="app-brand__icon" />
          <span>HR Policy Assistant</span>
        </Link>
        <ul className="menu-bar">
            {links.map((link) => (
              <li key={link.path}>
                <NavLink to={link.path} end={link.path === '/'} className="menu-bar__link">{link.label}</NavLink>
              </li>
            ))}
            <li>
              {isLoggedIn ? (
                <button
                  type="button"
                  className="menu-bar__link"
                  onClick={() => {
                    if (window.confirm('Are you sure you want to logout?')) {
                      logout();
                    }
                  }}
                >
                  Logout
                </button>
              ) : (
                <NavLink to="/login" className="menu-bar__link">Login</NavLink>
              )}
            </li>
        </ul>
      </nav>

      <main className="app-main">
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
      </main>

      <AppFooter />
    </div>
  );
}
