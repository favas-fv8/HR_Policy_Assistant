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


      </div>
    </div>
  );
}
