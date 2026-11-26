export default function AboutPage() {
  return (
    <div className="neural-page about-page">
      <section className="neural-card neural-page__panel about-page__panel">
        <h1 className="neural-page__title">About HR Policy Assistant</h1>
        <p className="neural-page__text neural-page__text--lead">
          HR Policy Assistant is an intelligent platform designed to help employees and HR teams
          navigate company policies with ease. Our system combines semantic search with AI-powered
          assistance to provide accurate, source-cited answers from your policy document library.
        </p>
        <h2 className="neural-page__section-title">How HR Policy Assistant Works</h2>
        <p className="neural-page__text">
          Built with a modern React frontend and a Python backend, HR Policy Assistant processes
          uploaded documents into searchable embeddings. When an employee asks a question, the system
          retrieves the most relevant policy sections and presents them with exact source references,
          including document titles and page numbers.
        </p>
        <p className="neural-page__text neural-page__text--last">
          The platform supports role-based access control, ensuring that employees only see policies
          relevant to their department and role, while HR admins have full access to all documents
          and can manage the entire policy library.
        </p>
      </section>

      <section className="neural-card neural-page__panel about-page__panel">
        <h3 className="neural-page__card-title">Key Features</h3>
        <ul className="neural-page__list">
          <li>Intelligent semantic policy search</li>
          <li>AI-powered answers with source citations</li>
          <li>Centralized document library</li>
          <li>Role-based access control</li>
          <li>Secure employee access</li>
        </ul>
      </section>
    </div>
  );
}