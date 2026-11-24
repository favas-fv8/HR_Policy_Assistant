import { apiFetch } from './http';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';
const AUTH_HEADERS = (token: string | null) => ({ Authorization: `Bearer ${token ?? ''}` });

export const sendMessage = async (conversationId: number, content: string) => {
  const data = await apiFetch(`${API_BASE}/v1/chat/conversations/${conversationId}/send/`, {
    method: 'POST',
    headers: {
      ...AUTH_HEADERS(localStorage.getItem('hr_token')),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ content }),
  });
  return data;
};

export const fetchConversations = async (): Promise<any[]> => {
  const data = await apiFetch(`${API_BASE}/v1/chat/conversations/`, {
    headers: { ...AUTH_HEADERS(localStorage.getItem('hr_token')) },
  });
  return Array.isArray(data) ? data : [];
};

export const createConversation = async (title?: string) => {
  const data = await apiFetch(`${API_BASE}/v1/chat/conversations/new/`, {
    method: 'POST',
    headers: {
      ...AUTH_HEADERS(localStorage.getItem('hr_token')),
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ title: title || 'New Conversation' }),
  });
  return data;
};

export const fetchMessages = async (conversationId: number) => {
  const data = await apiFetch(`${API_BASE}/v1/chat/conversations/${conversationId}/messages/`, {
    headers: { ...AUTH_HEADERS(localStorage.getItem('hr_token')) },
  });
  return Array.isArray(data) ? data : [];
};
