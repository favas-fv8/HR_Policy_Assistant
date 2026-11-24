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
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      {!user ? (
        <div style={{ border: '2px solid #dc3545', borderRadius: '8px', padding: '2rem', textAlign: 'center', margin: '2rem 0' }}>
          <h3 style={{ color: '#dc3e50', marginBottom: '0.5rem' }}>Access Denied</h3>
          <p style={{ color: '#555', marginBottom: '1rem' }}>
            You must be logged in to view this page.
          </p>
          <button
            style={{
              padding: '0.5rem 1rem',
              background: '#2c3e50',
              color: '#fff',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
            }}
            onClick={() => navigate('/login')}
          >
            Login
          </button>
        </div>
      ) : user.role !== 'hr_admin' ? (
        <div style={{ border: '2px solid #dc3545', borderRadius: '8px', padding: '2rem', textAlign: 'center', margin: '2rem 0' }}>
          <h3 style={{ color: '#dc3e50', marginBottom: '0.5rem' }}>Access Denied</h3>
          <p style={{ color: '#555', marginBottom: '1rem' }}>
            You do not have HR Admin privileges to view this page.
          </p>
          <p style={{ color: '#555' }}>
            <Link to="/employee-dashboard" style={{ color: '#3498db' }}>Go to Employee Dashboard</Link>
            or <Link to="/login" style={{ color: '#3498db' }}>Logout</Link>.
          </p>
        </div>
      ) : (
        <>
          <section style={{ marginBottom: '2rem' }}>
            <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1a1a2e', marginBottom: '0.5rem' }}>
              HR Admin Dashboard
            </h1>
            <p style={{ color: '#52525b', marginBottom: '1.5rem' }}>
              Manage policy documents and view system analytics.
            </p>
          </section>

          <section>
            <h2 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '1rem' }}>
              Document Library
            </h2>

            {loading ? (
              <p>Loading documents...</p>
            ) : documents.length === 0 ? (
              <p style={{ color: '#666', marginBottom: '1.5rem' }}>
                No documents uploaded yet. <Link to="/documents" style={{ color: '#3498db' }}>Upload your first document</Link>.
              </p>
            ) : (
              <ul style={{ listStyle: 'none', padding: '0', margin: '0' }}>
                {documents.map((doc: any) => (
                  <li key={doc.id} style={{ display: 'flex', justifyContent: 'between', alignItems: 'center', padding: '0.75rem 0', borderBottom: '1px solid #eee' }}>
                    <span style={{ color: '#333' }}>{doc.title}</span>
                    <span style={{ color: '#666', marginLeft: '1rem' }}>({doc.page_count} pages)</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section style={{ marginTop: '1.5rem' }}>
            <Link
              to="/documents"
              style={{
                display: 'inline-block',
                padding: '0.5rem 1rem',
                background: '#3498db',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.9rem',
                cursor: 'pointer',
                textDecoration: 'none',
              }}
            >
              Go to Document Management
            </Link>
            <button
              onClick={loadDocuments}
              style={{
                padding: '0.5rem 1rem',
                background: 'transparent',
                border: '1px solid #ddd',
                color: '#555',
                borderRadius: '6px',
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              Refresh
            </button>
          </section>
        </>
      )}
    </div>
  );
}
