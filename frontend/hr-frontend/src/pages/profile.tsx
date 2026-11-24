import { useAuth } from '../state/authContext';
import { Link, useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  return (
    <div style={{ maxWidth: '760px', width: 'calc(100% - 2rem)', margin: '3rem auto', padding: '2rem', background: '#fff', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '1.5rem', color: '#2c3e50' }}>Profile</h2>
      <div style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.5rem', textAlign: 'left' }}>
        {[
          ['Username', user.username],
          ['Email', user.email],
          ['Role', user.role],
          ['Employee ID', user.employee_id],
        ].map(([label, value]) => (
          <div key={label} style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: '1rem', alignItems: 'start' }}>
            <strong style={{ color: '#2c3e50' }}>{label}:</strong>
            <span style={{ color: '#374151', wordBreak: 'break-word' }}>{value}</span>
          </div>
        ))}
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

    </div>
  );
}