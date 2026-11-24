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
            <div style={{
              padding: '1.25rem 1.5rem',
              borderRadius: '12px',
              background: '#fff',
              border: '1px solid #e5e7eb',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
            }}>
              <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1a1a2e', marginBottom: '0.5rem', marginTop: 0 }}>
                HR Admin Dashboard
              </h1>
              <p style={{ color: '#3f3f46', marginBottom: 0 }}>
                Manage policy documents and view system analytics.
              </p>
            </div>
          </section>

          <section style={{
            padding: '1.25rem 1.5rem',
            borderRadius: '12px',
            background: '#fff',
            border: '1px solid #e5e7eb',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
          }}>
            <h2 style={{ fontSize: '1.25rem', color: '#1f2937', marginBottom: '1rem', marginTop: 0 }}>
              Document Library
            </h2>

            {loading ? (
              <p style={{ color: '#374151', margin: 0 }}>Loading documents...</p>
            ) : documents.length === 0 ? (
              <p style={{ color: '#374151', marginBottom: '1.5rem' }}>
                No documents uploaded yet. <Link to="/documents" style={{ color: '#1d4ed8' }}>Upload your first document</Link>.
              </p>
            ) : (
              <ul style={{ listStyle: 'none', padding: '0', margin: '0' }}>
                {documents.map((doc: any) => (
                  <li key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderBottom: '1px solid rgba(255,255,255,0.35)' }}>
                    <span style={{ color: '#1f2937', fontWeight: 500 }}>{doc.title}</span>
                    <span style={{ color: '#374151', marginLeft: '1rem' }}>({doc.page_count} pages)</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
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
                background: '#6b7280',
                border: '1px solid #6b7280',
                color: '#fff',
                borderRadius: '6px',
                fontSize: '0.9rem',
                cursor: 'pointer',
                marginLeft: 'auto',
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
