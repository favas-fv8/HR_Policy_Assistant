import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Document,
  DocumentProcessingStatus,
  fetchDocumentChunks,
  fetchDocumentStatus,
  fetchDocuments,
  reprocessDocument,
  uploadDocument,
  deleteDocument,
} from '../services/documentService';
import { useAuth } from '../state/authContext';

export default function DocumentsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [documentsList, setDocumentsList] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [uploadTitle, setUploadTitle] = useState('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [viewingDoc, setViewingDoc] = useState<Document | null>(null);
  const [viewingChunks, setViewingChunks] = useState<any[] | null>(null);
  const [statusById, setStatusById] = useState<Record<number, DocumentProcessingStatus>>({});
  const pollRef = useRef<number | null>(null);
  const pollingIdRef = useRef<number | null>(null);
  const inFlightRef = useRef(false);

  const isAdmin = user?.role === 'hr_admin';

  const stopPolling = () => {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
    pollingIdRef.current = null;
    inFlightRef.current = false;
  };

  const mergeStatusIntoDoc = (doc: Document, st?: DocumentProcessingStatus): Document => {
    if (!st) return doc;
    return {
      ...doc,
      status: st.status,
      processing_progress: st.processing_progress,
      processing_stage: st.processing_stage,
      processing_stage_detail: st.processing_stage_detail,
      total_chunks: st.total_chunks,
      processed_chunks: st.processed_chunks,
      chunk_count: st.chunk_count ?? doc.chunk_count,
      page_count: st.page_count ?? doc.page_count,
      processing_error: st.processing_error ?? '',
    };
  };

  const isTerminalStatus = (status?: string) => status === 'ready' || status === 'completed' || status === 'error';

  const getDocStatus = (doc: Document) => statusById[doc.id] ? mergeStatusIntoDoc(doc, statusById[doc.id]) : doc;

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDocuments();
      setDocumentsList(Array.isArray(data) ? data : []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load documents.');
      setDocumentsList([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
    return () => stopPolling();
  }, []);

  useEffect(() => {
    const doc = viewingDoc;
    if (!doc) {
      stopPolling();
      return;
    }

    let cancelled = false;
    const docId = doc.id;

    const poll = async () => {
      if (cancelled || inFlightRef.current || pollingIdRef.current !== docId) return;
      inFlightRef.current = true;
      try {
        const st = await fetchDocumentStatus(docId);
        if (cancelled || pollingIdRef.current !== docId) return;
        setStatusById((prev) => ({ ...prev, [docId]: st }));
        setViewingDoc((prev) => (prev && prev.id === docId ? mergeStatusIntoDoc(prev, st) : prev));
        setDocumentsList((prev) => prev.map((d) => (d.id === docId ? mergeStatusIntoDoc(d, st) : d)));
        if (isTerminalStatus(st.status)) {
          stopPolling();
          // Refresh once for accurate chunk_count/chunks when done
          fetchDocumentChunks(docId).then((chunks) => {
            if (!cancelled && pollingIdRef.current == null) {
              setViewingChunks(Array.isArray(chunks) ? chunks : []);
            }
          }).catch(() => {});
          loadDocuments().catch(() => {});
        }
      } catch {
        // Keep last known state; avoid noisy UI on transient poll failures
      } finally {
        inFlightRef.current = false;
      }
    };

    stopPolling();
    pollingIdRef.current = docId;
    void poll();
    if (!isTerminalStatus(doc.status)) {
      pollRef.current = window.setInterval(poll, 1000);
    }

    return () => {
      cancelled = true;
      if (pollingIdRef.current === docId) stopPolling();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [viewingDoc?.id]);

  const handleUploadFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadFile(file);
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      return;
    }
    setUploading(true);
    setError(null);
    setSuccess(null);
    try {
      const title = uploadTitle.trim() || uploadFile.name.replace(/\.pdf$/i, '');
      await uploadDocument(uploadFile, title);
      setSuccess('Document uploaded successfully.');
      setUploadTitle('');
      setUploadFile(null);
      await loadDocuments();
    } catch (e: any) {
      setError(e?.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
    }
  };

  const handleViewDetails = async (doc: Document) => {
    setError(null);
    try {
      const [chunks, st] = await Promise.all([
        fetchDocumentChunks(doc.id),
        fetchDocumentStatus(doc.id).catch(() => null),
      ]);
      if (st) setStatusById((prev) => ({ ...prev, [doc.id]: st }));
      setViewingDoc(mergeStatusIntoDoc(doc, st || undefined));
      setViewingChunks(Array.isArray(chunks) ? chunks : []);
    } catch (e: any) {
      setError(e?.message || 'Failed to load document details.');
      setViewingDoc(null);
      setViewingChunks(null);
    }
  };

  const handleDelete = async (doc: Document) => {
    try {
      await deleteDocument(doc.id);
      setSuccess('Document deleted successfully.');
      setViewingDoc(null);
      setViewingChunks(null);
      await loadDocuments();
    } catch (e: any) {
      setError(e?.message || 'Failed to delete document.');
    }
  };

  const handleReprocess = async (doc: Document) => {
    setError(null);
    setSuccess(null);
    try {
      const resp = await reprocessDocument(doc.id);
      setSuccess(`Reprocessing started for "${doc.title}".`);
      const optimistic: DocumentProcessingStatus = {
        id: doc.id,
        title: doc.title,
        status: (resp?.status as any) || 'started',
        processing_progress: 10,
        processing_stage: 'started',
        processing_stage_detail: 'Reprocessing requested.',
        total_chunks: 0,
        processed_chunks: 0,
        chunk_count: 0,
        page_count: doc.page_count || 0,
        processing_error: '',
      };
      setStatusById((prev) => ({ ...prev, [doc.id]: optimistic }));
      setViewingDoc((prev) => (prev && prev.id === doc.id ? mergeStatusIntoDoc(prev, optimistic) : prev));
      await loadDocuments();
    } catch (e: any) {
      setError(e?.message || 'Failed to reprocess document.');
    }
  };

  return (
    <div className="documents-page" style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>Document Library</h2>
      {error && <p style={{ color: '#e74c32' }}>{error}</p>}
      {success && <p style={{ color: '#27ae60' }}>{success}</p>}

      {isAdmin && (
        <section style={{ background: '#fff', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', marginBottom: '2rem' }}>
          <h3 style={{ color: '#2c3e50', marginBottom: '1rem' }}>Upload HR Policy PDF</h3>
          <form onSubmit={handleUploadSubmit}>
            <input
              type="text"
              placeholder="Document title (optional)"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              style={{ width: '100%', padding: '0.6rem', border: '1px solid #ddd', borderRadius: '6px', fontSize: '0.95rem', marginBottom: '0.75rem' }}
            />
            <input
              type="file"
              accept=".pdf"
              onChange={handleUploadFileChange}
              disabled={uploading}
              style={{ marginBottom: '0.75rem' }}
            />
            <button type="submit" disabled={uploading || !uploadFile} style={{ padding: '0.6rem 1.2rem', background: '#2c3e50', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', marginTop: '0.5rem' }}>
              Upload
            </button>
          </form>
        </section>
      )}

      <section>
        <h3 style={{ color: '#2c3e50', marginBottom: '1rem' }}>Documents</h3>
        {loading ? (
          <p>Loading documents...</p>
        ) : documentsList.length === 0 ? (
          <p style={{ color: '#666' }}>No documents available.</p>
        ) : (
          <ul className="doc-list" style={{ listStyle: 'none', padding: '0' }}>
            {documentsList.map((rawDoc: Document) => {
              const doc = getDocStatus(rawDoc);
              return (
              <li key={doc.id} className="doc-item" style={{ padding: '0.75rem 0', borderBottom: '1px solid #eee' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ color: '#333', fontWeight: 500 }}>{doc.title}</span>
                    <span style={{ color: '#666', marginLeft: '0.75rem' }}>
                      ({(doc.page_count ?? 0)} pages)
                    </span>
                    <div style={{ color: '#666', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                      Status: {doc.status} | Progress: {doc.processing_progress ?? (doc.status === 'ready' ? 100 : 0)}% | Chunks: {doc.chunk_count ?? 0} | Attempt: {doc.processing_attempt ?? 0}
                    </div>
                  </div>
                  <div>
                    <button
                      type="button"
                      onClick={() => navigate(`/documents/${doc.id}/view`)}
                      style={{ marginRight: '0.5rem', padding: '0.4rem 0.8rem', background: '#3498db', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
                    >
                      View Document
                    </button>
                    {isAdmin && (
                      <>
                        <button type="button" onClick={() => handleViewDetails(doc)} style={{ marginRight: '0.5rem', padding: '0.4rem 0.8rem', background: '#64748b', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                          View Details
                        </button>
                        <button type="button" onClick={() => handleReprocess(doc)} style={{ marginRight: '0.5rem', padding: '0.4rem 0.8rem', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                          Retry
                        </button>
                        <button type="button" onClick={() => handleDelete(doc)} style={{ padding: '0.4rem 0.8rem', background: '#dc3545', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </div>
              </li>
            );
            })}
          </ul>
        )}
      </section>

      {viewingDoc && (() => {
        const st = statusById[viewingDoc.id];
        const doc = mergeStatusIntoDoc(viewingDoc, st);
        const progress = Math.max(0, Math.min(100, Number(doc.processing_progress ?? 0)));
        const stage = doc.processing_stage || (doc.status === 'ready' ? 'ready' : doc.status === 'error' ? 'error' : 'uploaded');
        const stages = [
          { key: 'uploaded', label: 'PDF uploaded' },
          { key: 'extracting', label: 'Text extraction' },
          { key: 'chunking', label: 'Text chunking' },
          { key: 'embedding', label: 'Embedding generation' },
          { key: 'storing', label: 'Embedding storage' },
          { key: 'ready', label: 'Ready for RAG' },
        ];
        const stageOrder = ['uploaded', 'started', 'extracting', 'chunking', 'embedding', 'storing', 'completed', 'ready'];
        const currentIdx = stageOrder.indexOf(stage);
        const stageState = (key: string) => {
          if (doc.status === 'error') {
            if (key === 'ready') return 'pending';
            const kIdx = stageOrder.indexOf(key);
            if (kIdx < currentIdx) return 'completed';
            if (kIdx === currentIdx || (stage === 'error' && kIdx === currentIdx - 1)) return 'current';
            return 'pending';
          }
          if (doc.status === 'ready' || doc.status === 'completed') return key === 'ready' ? 'completed' : 'completed';
          const kIdx = stageOrder.indexOf(key);
          if (key === 'ready') return 'pending';
          if (kIdx < currentIdx) return 'completed';
          if (kIdx === currentIdx || (stage === 'started' && key === 'uploaded')) return key === 'uploaded' && stage !== 'uploaded' ? 'completed' : 'current';
          return 'pending';
        };

        return (
          <section style={{ marginTop: '2rem', background: '#fff', padding: '1.5rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem' }}>
              <h3 style={{ color: '#2c3e50', margin: 0 }}>Document Details: {doc.title}</h3>
              <button type="button" onClick={() => { setViewingDoc(null); setViewingChunks(null); }} style={{ padding: '0.35rem 0.7rem', border: '1px solid #ccc', borderRadius: 6, background: '#fff', cursor: 'pointer' }}>Close</button>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, color: '#374151', fontSize: 14 }}>
                <span>Status: <strong style={{ textTransform: 'capitalize' }}>{doc.status}</strong></span>
                <span>{progress}%</span>
              </div>
              <div style={{ width: '100%', height: 12, background: '#e5e7eb', borderRadius: 999, overflow: 'hidden' }}>
                <div style={{ width: `${progress}%`, height: '100%', background: doc.status === 'error' ? '#dc2626' : '#2563eb', transition: 'width 300ms ease' }} />
              </div>
              <p style={{ color: '#555', marginTop: 8, marginBottom: 0 }}>
                {doc.processing_stage_detail || (doc.status === 'ready' ? 'Document ready for RAG.' : doc.status === 'error' ? 'Processing failed.' : 'Processing...')}
              </p>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <h4 style={{ color: '#2c3e50', marginBottom: 8 }}>Processing Stages</h4>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: 6 }}>
                {stages.map((s) => {
                  const state = stageState(s.key);
                  const color = state === 'completed' ? '#16a34a' : state === 'current' ? '#2563eb' : '#9ca3af';
                  const icon = state === 'completed' ? '[done]' : state === 'current' ? '[current]' : '[pending]';
                  return (
                    <li key={s.key} style={{ color, fontSize: 14 }}>
                      <span style={{ fontFamily: 'monospace', marginRight: 8 }}>{icon}</span>{s.label}
                    </li>
                  );
                })}
              </ul>
            </div>

            <div style={{ marginTop: '1rem', color: '#555' }}>
              <p style={{ margin: '0.25rem 0' }}><strong>Chunks created (DB stored):</strong> {doc.chunk_count ?? 0}</p>
              <p style={{ margin: '0.25rem 0' }}><strong>Processed chunks (embedded):</strong> {doc.processed_chunks ?? 0}</p>
              <p style={{ margin: '0.25rem 0' }}><strong>Total chunks (current attempt):</strong> {doc.total_chunks ?? 0}</p>
              <p style={{ margin: '0.25rem 0' }}>Processing attempt: {doc.processing_attempt ?? 0}</p>
              <p style={{ margin: '0.25rem 0' }}>Filename: {doc.filename}</p>
              <p style={{ margin: '0.25rem 0' }}>File size: {doc.file_size}</p>
              <p style={{ margin: '0.25rem 0' }}>Pages: {doc.page_count ?? 0}</p>
            </div>

            {isAdmin && doc.status === 'error' && doc.processing_error ? (
              <div style={{ marginTop: '0.75rem', padding: '0.75rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 6 }}>
                <p style={{ color: '#b91c1c', margin: 0 }}><strong>Processing error:</strong> {doc.processing_error}</p>
                <button type="button" onClick={() => handleReprocess(doc)} style={{ marginTop: 8, padding: '0.4rem 0.8rem', background: '#f59e0b', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer' }}>
                  Retry Processing
                </button>
              </div>
            ) : null}

            {viewingChunks && viewingChunks.length > 0 && (
              <div style={{ marginTop: '1rem' }}>
                <h4 style={{ color: '#2c3e50' }}>Chunks</h4>
                {viewingChunks.map((c: any) => (
                  <div key={c.chunk_index} style={{ marginBottom: '0.5rem', padding: '0.5rem', border: '1px solid #eee', borderRadius: '6px' }}>
                    <div>Chunk #{c.chunk_index} | Page {c.page_number} | Length {c.chunk_text_length}</div>
                    <div style={{ color: '#666', fontSize: '0.9rem' }}>{c.chunk_text}</div>
                  </div>
                ))}
              </div>
            )}
          </section>
        );
      })()}
    </div>
  );
}
