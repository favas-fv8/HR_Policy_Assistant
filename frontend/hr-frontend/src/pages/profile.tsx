import { useAuth } from '../state/authContext';
import { Link, useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  return (
    <div style={{ maxWidth: '500px', margin: '3rem auto', padding: '2rem', background: '#fff', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08), text-align: center' }}>
      <h2 style={{ marginBottom: '1.5rem', color: '#2c3e50' }}>Profile</h2>
      <div style={{ marginBottom: '1rem' }}>
        <strong>Username:</strong> {user.username}
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <strong>Email:</strong> {user.email}
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <strong>Role:</strong> {user.role}
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <strong>Employee ID:</strong> {user.employee_id}
      </div>
      <button
        style={{
          width: '100%',
          padding: '0.75rem',
          background: '#8e44ad',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          fontSize: '1rem',
          fontWeight: 500,
          cursor: 'pointer',
          marginTop: '1rem',
        }}
        onClick={() => navigate('/change-password')}
      >
        Change Password
      </button>
      <p style={{ marginTop: '1.5rem', color: '#666', fontSize: '0.9rem' }}>
        <Link to="/change-password" style={{ color: '#3498db' }}>Change Password</Link>
      </p>
    </div>
  );
}