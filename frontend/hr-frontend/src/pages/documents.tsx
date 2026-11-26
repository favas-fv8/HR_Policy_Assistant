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
    <div className="neural-page documents-page-neural">
      <div className="neural-card neural-page__panel">
        <h1 className="neural-page__title">Document Library</h1>
        {error && <p className="neural-page__message neural-page__message--error">{error}</p>}
        {success && <p className="neural-page__message neural-page__message--success">{success}</p>}
      </div>

      {isAdmin && (
        <section className="neural-card neural-page__panel">
          <h2 className="neural-page__section-title">Upload HR Policy PDF</h2>
          <form onSubmit={handleUploadSubmit}>
            <input
              type="text"
              placeholder="Document title (optional)"
              value={uploadTitle}
              onChange={(e) => setUploadTitle(e.target.value)}
              className="neural-input"
            />
            <input
              type="file"
              accept=".pdf"
              onChange={handleUploadFileChange}
              disabled={uploading}
              className="documents-page-neural__file"
            />
            <button type="submit" disabled={uploading || !uploadFile} className="neural-btn neural-btn--primary documents-page-neural__upload-btn">
              Upload
            </button>
          </form>
        </section>
      )}

      <section className="neural-card neural-page__panel">
        <h2 className="neural-page__section-title">Documents</h2>
        {loading ? (
          <p className="neural-page__muted">Loading documents...</p>
        ) : documentsList.length === 0 ? (
          <p className="neural-page__muted">No documents available.</p>
        ) : (
          <ul className="documents-page-neural__list">
            {documentsList.map((rawDoc: Document) => {
              const doc = getDocStatus(rawDoc);
              return (
              <li key={doc.id} className="documents-page-neural__item">
                <div className="documents-page-neural__item-row">
                  <div className="documents-page-neural__doc-main">
                    <span className="documents-page-neural__doc-title">{doc.title}</span>
                    <span className="documents-page-neural__doc-meta">
                      ({(doc.page_count ?? 0)} pages)
                    </span>
                    <div className="documents-page-neural__doc-status">
                      Status: {doc.status} | Progress: {doc.processing_progress ?? (doc.status === 'ready' ? 100 : 0)}% | Chunks: {doc.chunk_count ?? 0} | Attempt: {doc.processing_attempt ?? 0}
                    </div>
                  </div>
                  <div className={isAdmin ? "documents-page-neural__actions is-admin" : "documents-page-neural__actions"}>
                    <button
                      type="button"
                      onClick={() => navigate(`/documents/${doc.id}/view`)}
                      className="neural-btn neural-btn--primary neural-btn--sm documents-page-neural__view-btn"
                    >
                      View Document
                    </button>
                    {isAdmin && (
                      <>
                        <button type="button" onClick={() => handleViewDetails(doc)} className="neural-btn neural-btn--secondary neural-btn--sm documents-page-neural__action-gap">
                          View Details
                        </button>
                        <button type="button" onClick={() => handleReprocess(doc)} className="neural-btn neural-btn--accent neural-btn--sm documents-page-neural__action-gap">
                          Retry
                        </button>
                        <button type="button" onClick={() => handleDelete(doc)} className="neural-btn neural-btn--danger neural-btn--sm">
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
          <section className="neural-card neural-page__panel">
            <div className="documents-page-neural__detail-head">
              <h2 className="neural-page__section-title documents-page-neural__detail-title">Document Details: {doc.title}</h2>
              <button type="button" onClick={() => { setViewingDoc(null); setViewingChunks(null); }} className="neural-btn neural-btn--secondary neural-btn--sm">Close</button>
            </div>

            <div className="documents-page-neural__section">
              <div className="documents-page-neural__progress-meta">
                <span>Status: <strong className="documents-page-neural__status">{doc.status}</strong></span>
                <span>{progress}%</span>
              </div>
              <div className="documents-page-neural__progress">
                <div style={{ width: `${progress}%`, height: '100%', background: doc.status === 'error' ? '#dc2626' : '#2563eb', transition: 'width 300ms ease' }} />
              </div>
              <p className="neural-page__muted documents-page-neural__stage-text">
                {doc.processing_stage_detail || (doc.status === 'ready' ? 'Document ready for RAG.' : doc.status === 'error' ? 'Processing failed.' : 'Processing...')}
              </p>
            </div>

            <div className="documents-page-neural__section">
              <h3 className="neural-page__card-title">Processing Stages</h3>
              <ul className="documents-page-neural__stages">
                {stages.map((s) => {
                  const state = stageState(s.key);
                  const color = state === 'completed' ? '#16a34a' : state === 'current' ? '#2563eb' : '#9ca3af';
                  const icon = state === 'completed' ? '[done]' : state === 'current' ? '[current]' : '[pending]';
                  return (
                    <li key={s.key} className="documents-page-neural__stage" style={{ color }}>
                      <span className="documents-page-neural__stage-icon">{icon}</span>{s.label}
                    </li>
                  );
                })}
              </ul>
            </div>

            <div className="documents-page-neural__meta-block">
              <p className="documents-page-neural__meta-line"><strong>Original PDF file size:</strong> {doc.file_size ?? 0} bytes ({((doc.file_size ?? 0) / 1024).toFixed(1)} KB)</p>
              <p className="documents-page-neural__meta-line"><strong>Extracted text (normalized):</strong> {doc.extracted_characters ?? 0} chars / {doc.extracted_tokens ?? 0} est. tokens{doc.extraction_tokenizer ? ` (${doc.extraction_tokenizer})` : ' (tokenizer unknown/legacy)'}</p>
              <p className="documents-page-neural__meta-line"><strong>Total chunks stored (DB):</strong> {doc.chunk_count ?? 0}</p>
              <p className="documents-page-neural__meta-line"><strong>Embedded chunks:</strong> {doc.embedded_chunk_count ?? doc.processed_chunks ?? 0}</p>
              <p className="documents-page-neural__meta-line"><strong>Total chunks (current attempt):</strong> {doc.total_chunks ?? 0}</p>
              <p className="documents-page-neural__meta-line">Pages: {doc.page_count ?? 0} | Attempt: {doc.processing_attempt ?? 0}</p>
              <p className="neural-page__muted neural-page__muted--small">Note: file bytes, extracted characters, token estimates, and chunk count are different metrics.</p>
            </div>

            {isAdmin && doc.status === 'error' && doc.processing_error ? (
              <div className="neural-alert neural-alert--error">
                <p className="neural-alert__text"><strong>Processing error:</strong> {doc.processing_error}</p>
                <button type="button" onClick={() => handleReprocess(doc)} className="neural-btn neural-btn--accent neural-btn--sm documents-page-neural__reprocess">
                  Retry Processing
                </button>
              </div>
            ) : null}

            {viewingChunks && viewingChunks.length > 0 && (
              <div className="documents-page-neural__section">
                <h3 className="neural-page__card-title">Chunks ({viewingChunks.length})</h3>
                <div className="documents-page-neural__chunks">
                  {viewingChunks.map((c: any) => (
                    <div key={c.chunk_index} className="documents-page-neural__chunk">
                      <div className="documents-page-neural__chunk-head">
                        <strong>Chunk #{c.chunk_index}</strong> | Pages {c.page_start ?? c.page_number}-{c.page_end ?? c.page_number}
                        {c.section_heading ? ` | ${c.section_heading}` : ''}
                      </div>
                      <div className="documents-page-neural__chunk-meta">
                        {c.char_count ?? c.chunk_text_length ?? 0} chars | {c.token_count ?? 0} est. tokens | embedding: {c.embedding_status || 'unknown'}
                      </div>
                      <div className="documents-page-neural__chunk-text">{c.chunk_text_preview || c.chunk_text || ''}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </section>
        );
      })()}
    </div>
  );
}
