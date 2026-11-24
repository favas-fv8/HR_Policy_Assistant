export default function HomePage() {

  return (
    <div>
      <div style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
        <section style={{ textAlign: 'left', marginBottom: '3rem' }}>
          <div style={{
            display: 'block',
            width: '100%',
            boxSizing: 'border-box',
            padding: '1.5rem 2rem',
            borderRadius: '16px',
            background: 'rgba(255, 255, 255, 0.35)',
            backdropFilter: 'blur(12px)',
            WebkitBackdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.45)',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
          }}>
            <h1 style={{ fontSize: '48px', fontWeight: 600, letterSpacing: '-1.68px', color: '#1a1a2e', marginBottom: '0.5rem', marginTop: 0 }}>
              HR Policy Assistant
            </h1>
            <p style={{ fontSize: '1.25rem', color: '#3f3f46', lineHeight: '1.6', margin: 0 }}>
              Intelligent search and assistance for HR policies. Find, understand, and comply with company policies instantly.
            </p>
          </div>
        </section>

        <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit', gap: '1.5rem', maxWidth: '1200px', margin: '0 auto' }}>
          <div style={{ background: '#f5f5f5', borderRadius: '12px', padding: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', transition: 'transform 0.2s' }}>
            <h3 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '0.5rem' }}>HR Policy Search</h3>
            <p style={{ color: '#666', lineHeight: '1.5' }}>Search across all uploaded policy documents with intelligent query understanding.</p>
          </div>
          <div style={{ background: '#f5f5f5', borderRadius: '12px', padding: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', transition: 'transform 0.2s' }}>
            <h3 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '0.5rem' }}>AI-Powered Policy Assistance</h3>
            <p style={{ color: '#666', lineHeight: '1.5' }}>Get AI-generated answers with source citations from your HR policy library.</p>
          </div>
          <div style={{ background: '#f5f5f5', borderRadius: '12px', padding: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', transition: 'transform 0.2s' }}>
            <h3 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '0.5rem' }}>Document Library</h3>
            <p style={{ color: '#666', lineHeight: '1.5' }}>Upload, organize, and manage HR policy documents in a centralized repository.</p>
          </div>
          <div style={{ background: '#f5f5f5', borderRadius: '12px', padding: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', transition: 'transform 0.2s' }}>
            <h3 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '0.5rem' }}>Source-Based Answers</h3>
            <p style={{ color: '#666', lineHeight: '1.5' }}>Every answer includes document references and page numbers for verification.</p>
          </div>
          <div style={{ background: '#f5f5f5', borderRadius: '12px', padding: '2rem', boxShadow: '0 4px 12px rgba(0,0,0,0.08)', transition: 'transform 0.2s' }}>
            <h3 style={{ fontSize: '1.25rem', color: '#2c3e50', marginBottom: '0.5rem' }}>Secure Employee Access</h3>
            <p style={{ color: '#666', lineHeight: '1.5' }}>Role-based access ensures employees only see policies relevant to their role.</p>
          </div>
        </section>

        <section style={{ margin: '3rem 0', padding: '2rem', background: '#f5f5f5', borderRadius: '12px', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}>
          <h2 style={{ fontSize: '1.5rem', color: '#2c3e50', marginBottom: '1rem' }}>How It Works</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit', gap: '2rem', maxWidth: '1200px' }}>
            <div>
              <h3 style={{ fontSize: '1.1rem', color: '#2c3e50', marginBottom: '0.5rem' }}>1</h3>
              <p style={{ color: '#666', lineHeight: '1.5' }}>HR Admin uploads policy documents to the system.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', color: '#2c3e50', marginBottom: '0.5rem' }}>2</h3>
              <p style={{ color: '#666', lineHeight: '1.5' }}>System processes and indexes the documents for semantic search.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', color: '#2c3e50', marginBottom: '0.5rem' }}>3</h3>
              <p style={{ color: '#666', lineHeight: '1.5' }}>Employees ask questions about HR policies in the chat interface.</p>
            </div>
            <div>
              <h3 style={{ fontSize: '1.1rem', color: '#2c3e50', marginBottom: '0.5rem' }}>4</h3>
              <p style={{ color: '#666', lineHeight: '1.5' }}>Assistant retrieves relevant policy information and provides answers with verified sources.</p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
