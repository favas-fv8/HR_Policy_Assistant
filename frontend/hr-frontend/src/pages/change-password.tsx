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
    <div className="neural-page neural-page--narrow profile-page-neural">
      <section className="neural-card neural-page__panel">
        <h1 className="neural-page__title neural-page__title--center">Change Password</h1>
        {error && <p className="neural-page__message neural-page__message--error">{error}</p>}
        {success && <p className="neural-page__message neural-page__message--success">{success}</p>}
        <form onSubmit={handleChangePassword} className="profile-page-neural__form">
          <input className="neural-input" type="password" placeholder="Current password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
          <input className="neural-input" type="password" placeholder="New password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
          <input className="neural-input" type="password" placeholder="Confirm new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} required />
          <button type="submit" disabled={isSubmitting} className="neural-btn neural-btn--primary profile-page-neural__action">
            {isSubmitting ? 'Updating...' : 'Update Password'}
          </button>
        </form>
        <p className="neural-page__footer-text">
          <Link to="/profile" className="neural-link">Back to Profile</Link>
        </p>
      </section>
    </div>
  );
}
