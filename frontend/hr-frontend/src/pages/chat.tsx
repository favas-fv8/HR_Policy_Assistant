import { useState, useEffect, useRef } from 'react';
import {
  sendMessage,
  fetchConversations,
  createConversation,
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
      try {
        const list = await loadConversations();
        if (list.length > 0) {
          const cid = list[0].id;
          setSelectedConversationId(cid);
          await loadMessages(cid);
        } else {
          const created = await createConversation();
          const cid2 = created?.id;
          setSelectedConversationId(cid2 ?? null);
          if (cid2) {
            await loadMessages(cid2);
          }
        }
      } catch (e: any) {
        setError(e?.message || 'Failed to load conversations.');
      }
    })();

    return () => {};
  }, []);

  const handleCreateConversation = async () => {
    try {
      const created = await createConversation();
      const cid = created?.id;
      if (cid) {
        setSelectedConversationId(cid);
        setMessages([]);
      }
      const list = await loadConversations();
      const createdList = Array.isArray(list) ? list : [];
      const target = createdList.find((c) => c.id === cid);
      if (target) {
        await loadMessages(cid);
      }
    } catch (e: any) {
      setError(e?.message || 'Failed to create conversation.');
    }
  };

  const handleSelectConversation = async (cid: number) => {
    setSelectedConversationId(cid);
    setError(null);
    await loadMessages(cid);
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !selectedConversationId || sending) return;
    const content = input.trim();
    setSending(true);
    setError(null);
    const userMsg: ChatMessage = { role: 'user', content };
    try {
      const assistantResp = await sendMessage(selectedConversationId, content);
      const assistantContent = assistantResp?.content ?? 'I apologize, but I was unable to generate a response.';
      const sources: Source[] = normalizeSources(assistantResp?.sources);
      setMessages((prev) => [...prev, userMsg, { role: 'assistant', content: assistantContent, sources }]);
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
    <div style={{ maxWidth: '1320px', margin: '2rem auto', padding: '0 1rem' }}>
      <div style={{ background: '#fff', padding: '1rem 1.5rem', borderRadius: '8px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', marginBottom: '1rem' }}>
        <h2 style={{ margin: 0, color: '#2c3e50' }}>AI Chatbot</h2>
      </div>
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        <div style={{ width: '260px', flexShrink: 0 }}>
          <button
            style={{
              marginBottom: '1rem',
              padding: '0.5rem 1rem',
              width: '100%',
              boxSizing: 'border-box',
              background: '#3498db',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              fontSize: '0.9rem',
              cursor: 'pointer',
            }}
            onClick={handleCreateConversation}
          >
            New Chat
          </button>
          <div style={{ border: '1px solid #ddd', borderRadius: '8px', background: '#fff', maxHeight: '480px', overflowY: 'auto' }}>
            {conversations.length === 0 ? (
              <p style={{ padding: '1rem', color: '#666', fontSize: '0.9rem' }}>No conversations yet.</p>
            ) : (
              conversations.map((c) => (
                <div
                  key={c.id}
                  onClick={() => handleSelectConversation(c.id)}
                  style={{
                    padding: '0.75rem 1rem',
                    cursor: 'pointer',
                    borderBottom: '1px solid #eee',
                    background: selectedConversationId === c.id ? '#eaf2f8' : '#fff',
                  }}
                >
                  <div style={{ fontWeight: selectedConversationId === c.id ? 600 : 400, color: '#333' }}>{c.title}</div>
                  <div style={{ fontSize: '0.75rem', color: '#888', marginTop: '0.25rem' }}>{formatUpdatedAt(c.updated_at)}</div>
                </div>
              ))
            )}
          </div>
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div className="messages cb-05__stage" style={{ minHeight: '400px', height: '520px', overflowY: 'auto', padding: '1.25rem', border: '1px solid #ddd', borderRadius: '14px', background: '#fff', marginBottom: '1rem' }}>
            <div className="cb-05__thread">
              {messages.length === 0 ? (
                <p style={{ color: '#8b93a7', textAlign: 'center', marginTop: '6rem' }}>Start a new conversation or select a previous one.</p>
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

          {error && <p style={{ color: '#e74c32', marginBottom: '0.75rem' }}>{error}</p>}

          <form onSubmit={handleSend} style={{ display: 'flex', gap: '0.5rem', background: '#fff', padding: '0.75rem', borderRadius: '20px', border: '1px solid #ddd' }}>
            <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask about HR policies..." autoFocus style={{ flex: 1, padding: '0.5rem', border: 'none', borderRadius: '15px', fontSize: '1rem' }} />
            <button type="submit" disabled={sending || !input.trim()} style={{ padding: '0 1.5rem', background: '#2c3e50', color: '#fff', border: 'none', borderRadius: '15px', fontWeight: 500, cursor: sending ? 'wait' : 'pointer' }}>
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
