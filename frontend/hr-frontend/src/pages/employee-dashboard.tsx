import { useAuth } from '../state/authContext';
import { Link, useNavigate } from 'react-router-dom';
import { fetchDocuments } from '../services/documentService';
import { useState, useEffect } from 'react';

export default function EmployeeDashboard() {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadDocuments = () => {
    setLoading(true);
    fetchDocuments()
      .then((data) => setDocuments(Array.isArray(data) ? data : []))
      .catch(() => setDocuments([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (user?.role === 'employee') {
      loadDocuments();
    } else {
      setLoading(false);
    }
  }, [user, token]);

  return (
    <div className="employee-home">
      {!user ? (
        <div className="neural-card employee-home__panel employee-home__panel--center">
          <h3 className="employee-home__error-title">Access Denied</h3>
          <p className="employee-home__muted">You must be logged in to view this page.</p>
          <button className="neural-btn neural-btn--primary" onClick={() => navigate('/login')}>Login</button>
        </div>
      ) : user.role !== 'employee' ? (
        <div className="neural-card employee-home__panel employee-home__panel--center">
          <h3 className="employee-home__error-title">Access Denied</h3>
          <p className="employee-home__muted">You do not have employee privileges to view this page.</p>
          <p className="employee-home__muted">
            <Link to="/hr-admin-dashboard" className="neural-link">Go to HR Admin Dashboard</Link>
            {' '}or <Link to="/login" className="neural-link">Logout</Link>.
          </p>
        </div>
      ) : (
        <>
          <section className="neural-card employee-home__panel">
            <h1 className="employee-home__title">Employee Dashboard</h1>
            <p className="employee-home__muted">Your personalized HR policy access.</p>
          </section>

          <section className="neural-card employee-home__panel">
            <h2 className="employee-home__section-title">Available Policies</h2>
            {loading ? (
              <p className="employee-home__muted">Loading policies...</p>
            ) : documents.length === 0 ? (
              <p className="employee-home__muted">No policies available for your role. Contact HR if you believe this is incorrect.</p>
            ) : (
              <ul className="employee-home__list">
                {documents.map((doc: any) => (
                  <li key={doc.id} className="employee-home__list-item">
                    <span className="employee-home__doc-title">{doc.title}</span>
                    <span className="employee-home__doc-meta">({doc.page_count} pages)</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="employee-home__actions">
            <button className="neural-btn neural-btn--primary" onClick={() => navigate('/chat')}>Ask a Question</button>
            <button className="neural-btn neural-btn--secondary" onClick={loadDocuments}>Refresh</button>
          </section>
        </>
      )}
    </div>
  );
}
