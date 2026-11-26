export default function HomePage() {
  return (
    <div className="neural-home">
      <aside className="neural-home__left">
        <div className="neural-home__brand">HR Policy Assistant.</div>
        <h1 className="neural-home__headline">Intelligent search and assistance for HR policies.</h1>
        <p className="neural-home__sub">Find, understand, and comply with company policies instantly with source-grounded answers.</p>
        <div className="neural-home__tags">
          <span className="neural-home__tag-label">Active Modules</span>
          <span className="neural-home__pill">N°Policy Search</span>
          <span className="neural-home__pill">S°AI Assistant</span>
          <span className="neural-home__pill">N°Compliance</span>
        </div>
      </aside>
      <section className="neural-home__feed">
        <article className="neural-card">
          <div className="neural-card__connector" />
          <header className="neural-card__header">
            <div className="neural-card__user">
              <div className="neural-card__avatar neural-card__avatar--icon"><img src="/images/icon-image.png" alt="" /></div>
              <div>
                <div className="neural-card__name">Policy Knowledge Base</div>
                <div className="neural-card__handle">Centralized • Verified</div>
              </div>
            </div>
            <div className="neural-card__id">ID: DOC-LIB</div>
          </header>
          <div className="neural-card__content">Upload, organize, and manage HR policy documents in a secure repository. The assistant retrieves relevant context from your approved policy library.</div>
        </article>
        <article className="neural-card">
          <div className="neural-card__connector" />
          <header className="neural-card__header">
            <div className="neural-card__user">
              <div className="neural-card__avatar neural-card__avatar--icon"><img src="/images/icon-image.png" alt="" /></div>
              <div>
                <div className="neural-card__name">AI-Grounded Answers</div>
                <div className="neural-card__handle">RAG • Citations</div>
              </div>
            </div>
            <div className="neural-card__id neural-card__id--accent">MODE: RAG</div>
          </header>
          <div className="neural-card__content">Employees ask natural-language questions and receive answers grounded in policy documents, with source references for verification.</div>
          <div className="neural-card__media"><div className="neural-data-vis"><div className="neural-data-wave" /></div></div>
        </article>
        <article className="neural-card">
          <div className="neural-card__connector" />
          <header className="neural-card__header">
            <div className="neural-card__user">
              <div className="neural-card__avatar neural-card__avatar--icon"><img src="/images/icon-image.png" alt="" /></div>
              <div>
                <div className="neural-card__name">Secure Access Control</div>
                <div className="neural-card__handle">Role-based • Auditable</div>
              </div>
            </div>
            <div className="neural-card__id">ID: AUTH</div>
          </header>
          <div className="neural-card__content">Role-based access ensures employees and HR admins see the appropriate tools and information while keeping policy operations secure.</div>
        </article>
      </section>
    </div>
  );
}
