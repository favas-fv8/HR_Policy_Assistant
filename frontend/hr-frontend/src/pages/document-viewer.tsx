import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { getDocumentFileBlobUrl, fetchDocuments } from '../services/documentService';

export default function DocumentViewerPage() {
  const { id } = useParams();
  const [search] = useSearchParams();
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [title, setTitle] = useState<string>('Document');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const page = Number(search.get('page') || '');

  useEffect(() => {
    let revoked: string | null = null;
    const docId = Number(id);
    if (!Number.isInteger(docId) || docId <= 0) {
      setError('Invalid document ID.');
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const docs = await fetchDocuments();
        const doc = docs.find((d) => d.id === docId);
        if (doc) setTitle(doc.filename || doc.title || `Document ${docId}`);
        const url = await getDocumentFileBlobUrl(docId);
        revoked = url;
        setBlobUrl(url);
      } catch (e: any) {
        setError(e?.message || 'Failed to load document.');
      } finally {
        setLoading(false);
      }
    })();
    return () => { if (revoked) URL.revokeObjectURL(revoked); };
  }, [id]);

  const pageParam = Number.isInteger(page) && page > 0 ? `page=${page}&` : '';
  const viewerSrc = blobUrl ? `${blobUrl}#${pageParam}view=FitH` : null;

  return (
    <div style={{ padding: '1rem', width: '100%', maxWidth: '100%', margin: '0 auto', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.25rem' }}>{title}</h2>
          {Number.isInteger(page) && page > 0 && <div style={{ color: '#52525b', fontSize: '0.9rem' }}>Page {page}</div>}
        </div>
        <Link to="/documents" style={{ color: '#2563EB', textDecoration: 'none' }}>Back to Documents</Link>
      </div>
      {loading && <p>Loading document...</p>}
      {error && <p style={{ color: '#b91c1c' }}>{error}</p>}
      {viewerSrc && (
        <iframe
          title={title}
          src={viewerSrc}
          style={{ width: '100%', height: '75vh', border: '1px solid #d4d4d8', borderRadius: 8, background: '#fff' }}
        />
      )}
    </div>
  );
}
