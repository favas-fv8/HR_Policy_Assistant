import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Source {
  document_id?: number | string | null;
  document_title?: string;
  page_number?: number | string | null;
  excerpt?: string;
}

interface Props {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

const asText = (value: unknown) => (typeof value === 'string' ? value : String(value ?? ''));

const getDocumentId = (documentId: unknown) => {
  if (documentId === null || documentId === undefined || documentId === '') return null;
  const n = Number(documentId);
  return Number.isInteger(n) && n > 0 ? n : null;
};

const getPage = (page: unknown) => {
  if (page === null || page === undefined || page === '') return null;
  const n = Number(page);
  return Number.isInteger(n) && n > 0 ? n : null;
};

export default function ChatMessageContent({ role, content, sources = [] }: Props) {
  if (role === 'user') {
    return <div style={{ whiteSpace: 'pre-wrap' }}>{content}</div>;
  }

  const validSources = (Array.isArray(sources) ? sources : []).filter(
    (s): s is Source => !!s && typeof s === 'object'
  );

  return (
    <div className="chat-answer-wrap">
      <div className="chat-answer-section">
        <div className="chat-section-label">Answer</div>
        <div className="chat-md">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            skipHtml
            components={{
              a: ({ href, children }) => {
                const url = asText(href);
                const allowed = url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/');
                if (!allowed) return <span>{children}</span>;
                return <a href={url} target="_blank" rel="noreferrer noopener">{children}</a>;
              },
              table: ({ children }) => <div className="chat-table-wrap"><table>{children}</table></div>,
            }}
          >
            {content || ''}
          </ReactMarkdown>
        </div>
      </div>

      {validSources.length > 0 && (
        <div className="chat-sources" aria-label="Sources">
          <div className="chat-section-label chat-sources-label">Sources</div>
          <div className="chat-sources-list">
            {validSources.map((s, i) => {
              const title = asText(s.document_title || 'Unknown document');
              const docId = getDocumentId(s.document_id);
              const page = getPage(s.page_number);
              const href = docId ? `/documents/${docId}/view${page ? `?page=${page}` : ''}` : null;
              return (
                <div key={`${title}-${docId ?? 'x'}-${page ?? 'na'}-${i}`} className="chat-source-card">
                  <div className="chat-source-meta">
                    <span className="chat-source-pdf" aria-hidden="true">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/><path d="M9 15h6"/><path d="M9 18h4"/>
                      </svg>
                    </span>
                    {href ? (
                      <a href={href} target="_blank" rel="noreferrer noopener" className="chat-source-link">{title}</a>
                    ) : (
                      <span className="chat-source-missing" title="Source document unavailable">{title} (unavailable)</span>
                    )}
                  </div>
                  <div className="chat-source-page">Page {page ?? 'N/A'}</div>
                  {s.excerpt ? <div className="chat-source-excerpt">{asText(s.excerpt)}</div> : null}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
