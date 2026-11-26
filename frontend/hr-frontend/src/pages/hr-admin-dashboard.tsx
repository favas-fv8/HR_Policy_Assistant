import { useAuth } from '../state/authContext';
import { Link, useNavigate } from 'react-router-dom';
import { fetchDocuments } from '../services/documentService';
import { useState, useEffect } from 'react';

export default function HRAdminDashboard() {
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
    if (user?.role === 'hr_admin') {
      loadDocuments();
    } else {
      setLoading(false);
    }
  }, [user, token]);

  return (
    <div className="hr-admin-home">
      {!user ? (
        <div className="neural-card hr-admin-home__panel hr-admin-home__panel--center">
          <h3 className="hr-admin-home__error-title">Access Denied</h3>
          <p className="hr-admin-home__muted">You must be logged in to view this page.</p>
          <button className="neural-btn neural-btn--primary" onClick={() => navigate('/login')}>
            Login
          </button>
        </div>
      ) : user.role !== 'hr_admin' ? (
        <div className="neural-card hr-admin-home__panel hr-admin-home__panel--center">
          <h3 className="hr-admin-home__error-title">Access Denied</h3>
          <p className="hr-admin-home__muted">You do not have HR Admin privileges to view this page.</p>
          <p className="hr-admin-home__muted">
            <Link to="/employee-dashboard" className="neural-link">Go to Employee Dashboard</Link>
            {' '}or <Link to="/login" className="neural-link">Logout</Link>.
          </p>
        </div>
      ) : (
        <>
          <section className="neural-card hr-admin-home__panel">
            <h1 className="hr-admin-home__title">HR Admin Dashboard</h1>
            <p className="hr-admin-home__subtitle">Manage policy documents and view system analytics.</p>
          </section>

          <section className="neural-card hr-admin-home__panel">
            <h2 className="hr-admin-home__section-title">Document Library</h2>

            {loading ? (
              <p className="hr-admin-home__muted">Loading documents...</p>
            ) : documents.length === 0 ? (
              <p className="hr-admin-home__muted">
                No documents uploaded yet. <Link to="/documents" className="neural-link">Upload your first document</Link>.
              </p>
            ) : (
              <ul className="hr-admin-home__list">
                {documents.map((doc: any) => (
                  <li key={doc.id} className="hr-admin-home__list-item">
                    <span className="hr-admin-home__doc-title">{doc.title}</span>
                    <span className="hr-admin-home__doc-meta">({doc.page_count} pages)</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="hr-admin-home__actions">
            <Link to="/documents" className="neural-btn neural-btn--primary hr-admin-home__action-link">
              Go to Document Management
            </Link>
            <button onClick={loadDocuments} className="neural-btn neural-btn--secondary">
              Refresh
            </button>
          </section>
        </>
      )}
    </div>
  );
}
