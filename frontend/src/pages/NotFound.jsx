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
