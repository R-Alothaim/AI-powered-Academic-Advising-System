import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function NotFound() {
  const { user } = useAuth();
  const dest = user ? '/dashboard/chats' : '/login';

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', background: '#0A1628',
      color: '#E2E8F0', fontFamily: 'Inter, sans-serif', padding: 32,
    }}>
      <h1 style={{
        fontFamily: 'Playfair Display, Georgia, serif', fontSize: 72,
        color: '#EAD27A', marginBottom: 8,
      }}>
        404
      </h1>
      <p style={{ color: 'rgba(160,190,255,0.6)', marginBottom: 24, fontSize: 16 }}>
        Page not found
      </p>
      <Link
        to={dest}
        style={{
          padding: '12px 24px', borderRadius: 10, textDecoration: 'none',
          background: 'linear-gradient(135deg, #2458D4, #1A3EA8)', color: '#fff',
          fontWeight: 600, fontSize: 14,
        }}
      >
        Go to {user ? 'Dashboard' : 'Login'}
      </Link>
    </div>
  );
