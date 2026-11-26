import { useState, useEffect, useRef } from 'react';
import {
  sendMessage,
  startConversation,
  fetchConversations,
  deleteConversation,
  fetchMessages,
} from '../services/chatService';
import ChatMessageContent from '../components/ChatMessageContent';

interface Source {
  document_id?: number | string | null;
  document_title?: string;
  page_number?: number | string | null;
  excerpt?: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

interface Conversation {
  id: number;
  title: string;
  updated_at?: string;
  employee_name?: string;
}

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bootstrapped = useRef(false);
  const startingRef = useRef(false);

  const loadConversations = async () => {
    try {
      const convs = await fetchConversations();
      const list = Array.isArray(convs) ? convs : [];
      setConversations(list);
      return list;
    } catch (e: any) {
      setError(e?.message || 'Failed to load conversations.');
      return [];
    }
  };

  const loadMessages = async (cid: number) => {
    try {
      const msgs = await fetchMessages(cid);
      const mapped = (Array.isArray(msgs) ? msgs : []).map((m: any) => ({
        role: m.role === 'assistant' ? ('assistant' as const) : ('user' as const),
        content: m.content ?? '',
        sources: normalizeSources(m.sources),
      }));
      setMessages(mapped);
    } catch (e: any) {
      setError(e?.message || 'Failed to load conversation.');
    }
  };

  useEffect(() => {
    if (bootstrapped.current) return;
    bootstrapped.current = true;
    (async () => {
      await loadConversations();
      // Default to draft (no conversation created)
      setSelectedConversationId(null);
      setMessages([]);
    })();
    return () => {};
  }, []);

  const handleCreateConversation = async () => {
    // If already in empty draft, do nothing (no new DB record, no API call)
    if (selectedConversationId === null && messages.length === 0) {
      return;
    }
    // Open fresh draft
    setSelectedConversationId(null);
    setMessages([]);
    setError(null);
  };

  const handleDeleteConversation = async (e: React.MouseEvent, cid: number) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    try {
      await deleteConversation(cid);
      await loadConversations();
      if (selectedConversationId === cid) {
        setSelectedConversationId(null);
        setMessages([]);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to delete conversation.');
    }
  };

  const handleSelectConversation = async (cid: number) => {
    setSelectedConversationId(cid);
    setError(null);
    await loadMessages(cid);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const content = input.trim();
    setSending(true);
    setError(null);

    // Draft: create conversation on first message
    if (selectedConversationId === null) {
      if (startingRef.current) {
        setSending(false);
        return;
      }
      startingRef.current = true;
      try {
        const resp = await startConversation(content);
        const newCid = resp?.conversation_id as number | undefined;
        const assistantContent = resp?.content ?? 'I apologize, but I was unable to generate a response.';
        const sources: Source[] = normalizeSources(resp?.sources);
        const conversationTitle = typeof resp?.conversation_title === 'string' ? resp.conversation_title : 'New Chat';

        const userMsg: ChatMessage = { role: 'user', content };
        setMessages([{ ...userMsg }, { role: 'assistant', content: assistantContent, sources }]);
        setInput('');

        if (newCid) {
          setSelectedConversationId(newCid);
          // Prepend new conversation to list
          setConversations((prev) => {
            const exists = prev.some((c) => c.id === newCid);
            const newConv: Conversation = resp?.conversation
              ? { ...resp.conversation }
              : { id: newCid, title: conversationTitle, updated_at: new Date().toISOString() };
            if (exists) return prev.map((c) => (c.id === newCid ? { ...c, ...newConv } : c));
            return [newConv, ...prev.filter((c) => c.id !== newCid)];
          });
          await loadConversations();
        } else {
          await loadConversations();
        }
      } catch (e: any) {
        setError(e?.message || 'Failed to send message.');
      } finally {
        startingRef.current = false;
        setSending(false);
      }
      return;
    }

    // Existing conversation
    const userMsg: ChatMessage = { role: 'user', content };
    try {
      const assistantResp = await sendMessage(selectedConversationId, content);
      const assistantContent = assistantResp?.content ?? 'I apologize, but I was unable to generate a response.';
      const sources: Source[] = normalizeSources(assistantResp?.sources);
      const conversationTitle = typeof assistantResp?.conversation_title === 'string' ? assistantResp.conversation_title : null;
      setMessages((prev) => [...prev, userMsg, { role: 'assistant', content: assistantContent, sources }]);
      if (conversationTitle) {
        setConversations((prev) => prev.map((c) => (c.id === selectedConversationId ? { ...c, title: conversationTitle } : c)));
      }
      setInput('');
      await loadConversations();
    } catch (e: any) {
      setError(e?.message || 'Failed to send message.');
    } finally {
      setSending(false);
    }
  };

  const normalizeSources = (raw: unknown): Source[] => {
    if (!Array.isArray(raw)) return [];
    return raw
      .filter((s): s is Record<string, unknown> => !!s && typeof s === 'object' && !Array.isArray(s))
      .map((s) => ({
        document_id: typeof s.document_id === 'number' || typeof s.document_id === 'string' ? s.document_id : null,
        document_title: typeof s.document_title === 'string' ? s.document_title : (typeof s.title === 'string' ? s.title : 'Unknown document'),
        page_number: typeof s.page_number === 'number' || typeof s.page_number === 'string' ? s.page_number : null,
        excerpt: typeof s.excerpt === 'string' ? s.excerpt : (typeof s.chunk_text === 'string' ? s.chunk_text : ''),
      }));
  };

  const formatUpdatedAt = (updatedAt?: string) => {
    if (!updatedAt) return '';
    const d = new Date(updatedAt);
    if (Number.isNaN(d.getTime())) return '';
    return d.toLocaleString();
  };

  return (
    <div className="neural-page chat-page-neural">
      <div className="neural-card neural-page__panel chat-page-neural__header">
        <h1 className="neural-page__title chat-page-neural__title">AI Chatbot</h1>
      </div>
      <div className="cb-05 chat-page-neural__layout">
        <div className="chat-page-neural__sidebar">
          <button className="neural-btn neural-btn--primary chat-page-neural__new-btn" onClick={handleCreateConversation}>
            New Chat
          </button>
          <div className="neural-card chat-page-neural__history">
            {conversations.length === 0 ? (
              <p className="neural-page__muted chat-page-neural__empty">No conversations yet.</p>
            ) : (
              conversations.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleSelectConversation(c.id)}
                  className={`chat-page-neural__conv ${selectedConversationId === c.id ? 'is-active' : ''}`}
                >
                  <div className="chat-page-neural__conv-main">
                    <div title={c.title} className="chat-page-neural__conv-title">{c.title}</div>
                    <div className="chat-page-neural__conv-date">{formatUpdatedAt(c.updated_at)}</div>
                  </div>
                  <button
                    type="button"
                    title="Delete conversation"
                    aria-label="Delete conversation"
                    onClick={(e) => handleDeleteConversation(e, c.id)}
                    className="chat-page-neural__delete"
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path>
                      <path d="M10 11v6"></path>
                      <path d="M14 11v6"></path>
                      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"></path>
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="chat-page-neural__main">
          <div className="messages cb-05__stage neural-card chat-page-neural__stage">
            <div className="cb-05__thread">
              {messages.length === 0 ? (
                <p className="neural-page__muted chat-page-neural__start">Start a new conversation or select a previous one.</p>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={`chat-msg cb-05__turn ${msg.role === 'user' ? 'chat-msg-user cb-05__turn--out' : 'chat-msg-assistant cb-05__turn--in'}`}>
                    {msg.role === 'assistant' && <div className="cb-05__avatar" aria-hidden="true">AI</div>}
                    <div className={`chat-bubble cb-05__msg ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}>
                      <ChatMessageContent role={msg.role} content={msg.content} sources={msg.sources} />
                    </div>
                  </div>
                ))
              )}
              {sending && (
                <div className="chat-msg cb-05__turn chat-msg-assistant cb-05__turn--in">
                  <div className="cb-05__avatar" aria-hidden="true">AI</div>
                  <div className="chat-bubble cb-05__msg chat-bubble-assistant">
                    <div className="chat-answer-section">Assistant is typing...</div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {error && <p className="neural-page__message neural-page__message--error">{error}</p>}

          <form onSubmit={handleSend} className="neural-card chat-page-neural__composer">
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about HR policies..." autoFocus className="chat-page-neural__input" />
            <button type="submit" disabled={sending || !input.trim()} className="neural-btn neural-btn--primary">
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
