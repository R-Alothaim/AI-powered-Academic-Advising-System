import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('ErrorBoundary caught:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', background: '#0A1628',
          color: '#E2E8F0', fontFamily: 'Inter, sans-serif', padding: 32,
        }}>
          <h1 style={{ fontFamily: 'Playfair Display, Georgia, serif', color: '#EAD27A', marginBottom: 12 }}>
            Something went wrong
          </h1>
          <p style={{ color: 'rgba(160,190,255,0.6)', marginBottom: 24, textAlign: 'center', maxWidth: 400 }}>
            An unexpected error occurred. Please refresh the page to try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: '12px 24px', borderRadius: 10, border: 'none', cursor: 'pointer',
              background: 'linear-gradient(135deg, #2458D4, #1A3EA8)', color: '#fff',
              fontWeight: 600, fontSize: 14, fontFamily: 'Inter, sans-serif',
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
