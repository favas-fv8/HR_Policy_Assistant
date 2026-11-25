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
          <h2 style={{ marginBottom: '1.5rem', color: '#2c3e50' }}>Login</h2>
          {error && <p style={{ color: '#e74c32', marginBottom: '1.5rem' }}>{error}</p>}
          <form onSubmit={handleLogin} style={{ width: '100%', maxWidth: '400px', margin: '0 auto' }}>
            <input type="text" placeholder="Enter your User ID" value={userId} onChange={(e) => setUserId(e.target.value)} required style={{ padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem', marginBottom: '0.5rem', width: '100%', boxSizing: 'border-box' }} />
            <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required style={{ padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '1rem', marginBottom: '1rem', width: '100%', boxSizing: 'border-box' }} />
            <button type="submit" disabled={isSubmitting} style={{ width: '100%', padding: '0.75rem', background: '#2c3e50', color: '#fff', border: 'none', borderRadius: '6px', fontSize: '1rem', fontWeight: 500, cursor: isSubmitting ? 'wait' : 'pointer' }}>
              Sign In
            </button>
          </form>
          <p style={{ marginTop: '1.5rem', color: '#666', fontSize: '0.9rem' }}>
            Don't have an account? Contact admin
          </p>
        </div>
      </div>
    </div>
  );
}
