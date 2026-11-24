export default function AboutPage() {

  return (
    <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '36px', fontWeight: 600, letterSpacing: '-0.72px', color: '#1a1a2e', marginBottom: '1rem' }}>
        About HR Policy Assistant
      </h1>

      <p style={{ fontSize: '1.1rem', color: '#52525b', lineHeight: '1.8', marginBottom: '2rem' }}>
        HR Policy Assistant is an intelligent platform designed to help employees and HR teams
        navigate company policies with ease. Our system combines semantic search with AI-powered
        assistance to provide accurate, source-cited answers from your policy document library.
      </p>

      <h2 style={{ fontSize: '1.5rem', color: '#2c3e50', margin: '2rem 0 1rem' }}>How HR Policy Assistant Works</h2>

      <p style={{ fontSize: '1.1rem', color: '#52525b', lineHeight: '1.8' }}>
        Built with a modern React frontend and a Python backend, HR Policy Assistant processes
        uploaded documents into searchable embeddings. When an employee asks a question, the system
        retrieves the most relevant policy sections and presents them with exact source references,
        including document titles and page numbers.
      </p>

      <p style={{ fontSize: '1.1rem', color: '#52525b', lineHeight: '1.8' }}>
        The platform supports role-based access control, ensuring that employees only see policies
        relevant to their department and role, while HR admins have full access to all documents
        and can manage the entire policy library.
      </p>

      <div style={{ margin: '3rem 0', padding: '2rem', background: '#f8f9fa', borderRadius: '8px' }}>
        <h3 style={{ fontSize: '1.2rem', color: '#2c3e50', marginBottom: '0.5rem' }}>Key Features</h3>
        <ul style={{ color: '#52525b', lineHeight: '1.8', margin: '0' }}>
          <li style={{ marginBottom: '0.5rem' }}>• Intelligent semantic policy search</li>
          <li style={{ marginBottom: '0.5rem' }}>• AI-powered answers with source citations</li>
          <li style={{ marginBottom: '0.5rem' }}>• Centralized document library</li>
          <li style={{ marginBottom: '0.5rem' }}>• Role-based access control</li>
          <li style={{ marginBottom: '0.5rem' }}>• Secure employee access</li>
        </ul>
      </div>

      <footer style={{ marginTop: '3rem', paddingTop: '2rem', borderTop: '1px solid #eee', textAlign: 'center', color: '#666', fontSize: '0.9rem' }}>
        2026 • HR Policy Assistant • All rights reserved
      </footer>
    </div>
  );
}