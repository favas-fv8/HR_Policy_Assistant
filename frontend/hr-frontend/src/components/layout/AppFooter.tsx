export default function AppFooter() {
  return (
    <footer
      style={{
        padding: '1.5rem 2rem',
        textAlign: 'center',
        color: '#fff',
        fontSize: '0.9rem',
        marginTop: 'auto',
        backgroundColor: '#1b2836',
        borderTop: '1px solid rgba(255,255,255,0.12)',
      }}
    >
      <span
        style={{
          display: 'inline-block',
          padding: '10px 18px',
          borderRadius: '25px',
          backgroundColor: 'rgba(0, 0, 0, .7)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
          color: '#fff',
          fontWeight: 600,
        }}
      >
        <strong>HR Policy Assistant</strong> • 2026 • Built for enterprise HR compliance
      </span>
    </footer>
  );
}
