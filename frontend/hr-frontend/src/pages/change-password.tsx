import { useAuth } from '../state/authContext';
import { useState } from 'react';
import { Link } from 'react-router-dom';
import { apiFetch, getErrorMessage } from '../services/http';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export default function ChangePasswordPage() {
  const { user, token } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!user) {
    return null;
  }

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!currentPassword) {
      setError('Please enter your current password.');
      return;
    }
    if (!newPassword) {
      setError('Please enter a new password.');
      return;
    }
    if (!confirmPassword) {
      setError('Please confirm your new password.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('New password and confirmation do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      const data = await apiFetch<{ detail?: string; error?: string; old_password?: string[]; new_password1?: string[]; new_password2?: string[]; non_field_errors?: string[] }>(
        `${API_BASE}/v1/auth/password/change/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token ?? ''}`,
          },
          body: JSON.stringify({
            old_password: currentPassword,
            new_password1: newPassword,
            new_password2: confirmPassword,
          }),
        },
      );
      setSuccess('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      void data;
    } catch (err: any) {
      setError(getErrorMessage(err?.data, err?.message || 'Failed to change password.', err?.status || 0));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '420px', margin: '5rem auto', padding: '2rem', background: '#fff', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', textAlign: 'center' }}>
      <h2 style={{ marginBottom: '1.5rem', color: '#2c3e50' }}>Change Password</h2>
      {error && <p style={{ color: '#e74c32', marginBottom: '1.5rem' }}>{error}</p>}
      {success && <p style={{ color: '#27ae60', marginBottom: '1.5rem' }}>{success}</p>}
      <form onSubmit={handleChangePassword} style={{ maxWidth: '300px', margin: '0 auto' }}>
        <input type="password" placeholder="Current password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required style={{ padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem', marginBottom: '0.5rem', width: '100%' }} />
        <input type="password" placeholder="New password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required style={{ padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem', marginBottom: '0.5rem', width: '100%' }} />
        <input type="password" placeholder="Confirm new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required style={{ padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem', marginBottom: '1rem', width: '100%' }} />
        <button type="submit" disabled={isSubmitting} style={{ width: '100%', padding: '0.75rem', background: '#2c3e50', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '1rem', fontWeight: 500, cursor: isSubmitting ? 'wait' : 'pointer' }}>
          Update Password
        </button>
      </form>
      <p style={{ marginTop: '1.5rem', color: '#666', fontSize: '0.9rem' }}>
        <Link to="/profile" style={{ color: '#3498db' }}>Back to Profile</Link>
      </p>
    </div>
  );
}
