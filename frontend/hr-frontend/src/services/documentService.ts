import { apiFetch } from './http';

export interface Document {
  id: number;
  title: string;
  filename: string;
  file_url: string;
  file_size: number;
  status: 'started' | 'processing' | 'completed' | 'ready' | 'error' | string;
  uploaded_by_name: string;
  uploaded_at: string;
  chunk_count: number;
  embedded_chunk_count?: number;
  page_count: number;
  extracted_characters?: number;
  extracted_tokens?: number;
  extraction_tokenizer?: string;
  processing_error?: string;
  processing_progress?: number;
  processing_stage?: string;
  processing_stage_detail?: string;
  total_chunks?: number;
  processed_chunks?: number;
  processing_attempt?: number;
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
}

export interface DocumentChunkInfo {
  chunk_index: number;
  page_number: number;
  page_start?: number;
  page_end?: number;
  section_heading?: string;
  char_count?: number;
  token_count?: number;
  embedding_status?: string;
  chunk_text_length?: number;
  chunk_text_preview?: string;
  document_title?: string;
}

export interface DocumentProcessingStatus {
  id: number;
  title: string;
  status: Document['status'];
  processing_progress: number;
  processing_stage: string;
  processing_stage_detail: string;
  total_chunks: number;
  processed_chunks: number;
  chunk_count: number;
  embedded_chunk_count?: number;
  extracted_characters?: number;
  extracted_tokens?: number;
  extraction_tokenizer?: string;
  page_count: number;
  file_size?: number;
  processing_error?: string;
  processing_attempt?: number;
  processing_started_at?: string | null;
  processing_completed_at?: string | null;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const AUTH_HEADERS = (token: string | null) => ({ Authorization: `Bearer ${token ?? ''}` });

export const fetchDocuments = async (): Promise<Document[]> => {
  const token = localStorage.getItem('hr_token');
  const data = await apiFetch(`${API_BASE}/v1/documents/`, {
    headers: { ...AUTH_HEADERS(token) },
  });
  return Array.isArray(data) ? data : [];
};

export const uploadDocument = async (file: File, title?: string) => {
  const token = localStorage.getItem('hr_token');
  const formData = new FormData();
  formData.append('file', file);
  if (title && title.trim()) {
    formData.append('title', title.trim());
  }

  const resp = await fetch(`${API_BASE}/v1/documents/`, {
    method: 'POST',
    headers: { ...AUTH_HEADERS(token) },
    body: formData,
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(data?.detail || data?.error || (Array.isArray(data?.title) ? data.title[0] : 'Upload failed.'));
  }
  return data;
};

export const deleteDocument = async (documentId: number) => {
  const token = localStorage.getItem('hr_token');
  const data = await apiFetch(`${API_BASE}/v1/documents/${documentId}/`, {
    method: 'DELETE',
    headers: { ...AUTH_HEADERS(token) },
  });
  return data;
};

export const reprocessDocument = async (documentId: number) => {
  const token = localStorage.getItem('hr_token');
  const data = await apiFetch(`${API_BASE}/v1/documents/${documentId}/reprocess/`, {
    method: 'POST',
    headers: { ...AUTH_HEADERS(token) },
  });
  return data;
};

export const fetchDocumentChunks = async (documentId: number) => {
  const token = localStorage.getItem('hr_token');
  const data = await apiFetch(`${API_BASE}/v1/documents/${documentId}/chunks/`, {
    headers: { ...AUTH_HEADERS(token) },
  });
  return Array.isArray(data) ? data : [];
};

export const fetchDocumentStatus = async (documentId: number): Promise<DocumentProcessingStatus> => {
  const token = localStorage.getItem('hr_token');
  return apiFetch(`${API_BASE}/v1/documents/${documentId}/status/`, {
    headers: { ...AUTH_HEADERS(token) },
  });
};

export const getDocumentFileBlobUrl = async (documentId: number): Promise<string> => {
  const token = localStorage.getItem('hr_token');
  const resp = await fetch(`${API_BASE}/v1/documents/${documentId}/file/`, {
    headers: { ...AUTH_HEADERS(token) },
  });
  if (!resp.ok) {
    const text = await resp.text().catch(() => '');
    let data: any = null;
    try { data = text ? JSON.parse(text) : null; } catch { data = null; }
    throw new Error(data?.detail || data?.error || `Failed to load document (${resp.status}).`);
  }
  const blob = await resp.blob();
  return URL.createObjectURL(blob.type ? blob : new Blob([blob], { type: 'application/pdf' }));
};
