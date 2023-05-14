import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { auth } from '../api/api';
import AuthBackground from '../components/AuthBackground';
import '../styles/auth-bg.css';

export default function OtpVerify() {
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';

  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleVerify = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await auth.verifyOtp(email, code);
      if (data.token) {
        setSession(data.token, data.user);
        navigate('/dashboard/chats', { replace: true });
      } else {
        navigate('/login', { replace: true });
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setSuccess('');
    try {
      await auth.resendOtp(email);
      setSuccess('A new code has been sent to your email.');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-page">
      <AuthBackground />

      <div className="card-wrap">
        <div className="auth-card">
