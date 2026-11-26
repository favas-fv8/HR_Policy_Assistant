import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../state/authContext';

export default function LoginPage() {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    const u = userId.trim();
    if (!u || !password) {
      setError('Enter your User ID and password.');
      return;
    }
    setIsSubmitting(true);
    try {
      const user = await login({ username: u, password });
      navigate(user.role === 'hr_admin' ? '/hr-admin-dashboard' : '/employee-dashboard', { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Invalid User ID or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="login-page-wrap">
      <div className="login-card">
        <div className="login-card__image" aria-hidden="true">
          <img src="/images/login-side-image.png" alt="" />
        </div>
        <div className="login-card__form">
          <h2 className="login-card__title">Login</h2>
          <p className="login-card__subtitle">Sign in to access HR policies and support.</p>
          {error && <p className="login-card__error" role="alert">{error}</p>}
          <form onSubmit={handleLogin} className="login-card__form-inner">
            <label className="login-card__label" htmlFor="login-userid">User ID</label>
            <input id="login-userid" className="neural-input login-card__input" type="text" placeholder="Enter your User ID" value={userId} onChange={(e) => setUserId(e.target.value)} required autoComplete="username" />
            <label className="login-card__label" htmlFor="login-password">Password</label>
            <input id="login-password" className="neural-input login-card__input" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete="current-password" />
            <button type="submit" disabled={isSubmitting} className="neural-btn neural-btn--primary login-card__submit">
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
          <p className="login-card__note">Don't have an account? Contact admin</p>
        </div>
      </div>
    </div>
  );
}
