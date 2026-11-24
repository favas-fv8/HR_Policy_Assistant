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
      ) : user.role !== 'employee' ? (
        <div style={{ border: '2px solid #dc3545', borderRadius: '8px', padding: '2rem', textAlign: 'center', margin: '2rem 0' }}>
          <h3 style={{ color: '#dc3e50', marginBottom: '0.5rem' }}>Access Denied</h3>
          <p style={{ color: '#555', marginBottom: '1rem' }}>
            You do not have employee privileges to view this page.
          </p>
          <p style={{ color: '#555' }}>
            <Link to="/hr-admin-dashboard" style={{ color: '#3498db' }}>Go to HR Admin Dashboard</Link>
            or <Link to="/login" style={{ color: '#3498db' }}>Logout</Link>.
          </p>
        </div>
      ) : (
        <>
          <section style={{ marginBottom: '2rem', background: '#fff', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <h1 style={{ fontSize: '32px', fontWeight: 600, color: '#1a1a2e', marginBottom: '0.5rem', marginTop: 0 }}>
              Employee Dashboard
            </h1>
            <p style={{ color: '#52525b', marginBottom: 0 }}>
              Your personalized HR policy access.
            </p>
          </section>

          <section style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <h2 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '1rem', marginTop: 0 }}>
              Available Policies
            </h2>

            {loading ? (
              <p>Loading policies...</p>
            ) : documents.length === 0 ? (
              <p style={{ color: '#666', marginBottom: '1.5rem' }}>
                No policies available for your role. Contact HR if you believe this is incorrect.
              </p>
            ) : (
              <ul style={{ listStyle: 'none', padding: '0', margin: '0' }}>
                {documents.map((doc: any) => (
                  <li key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 0', borderBottom: '1px solid #eee' }}>
                    <span style={{ color: '#333' }}>{doc.title}</span>
                    <span style={{ color: '#666', marginLeft: '1rem' }}>({doc.page_count} pages)</span>
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
            <button
              onClick={() => navigate('/chat')}
              style={{
                padding: '0.5rem 1rem',
                background: '#3498db',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              Ask a Question
            </button>
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
