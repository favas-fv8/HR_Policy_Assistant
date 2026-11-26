import { useAuth } from '../state/authContext';
import { useNavigate } from 'react-router-dom';

export default function ProfilePage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  if (!user) {
    return null;
  }

  return (
    <div className="neural-page neural-page--narrow profile-page-neural">
      <section className="neural-card neural-page__panel">
        <h1 className="neural-page__title neural-page__title--center">Profile</h1>
        <div className="profile-page-neural__grid">
          {[
            ['Username', user.username],
            ['Email', user.email],
            ['Role', user.role],
            ['Employee ID', user.employee_id],
          ].map(([label, value]) => (
            <div key={String(label)} className="profile-page-neural__row">
              <span className="profile-page-neural__label">{label}</span>
              <span className="profile-page-neural__value">{String(value)}</span>
            </div>
          ))}
        </div>
        <button className="neural-btn neural-btn--primary profile-page-neural__action" onClick={() => navigate('/change-password')}>
          Change Password
        </button>
      </section>
    </div>
  );
}