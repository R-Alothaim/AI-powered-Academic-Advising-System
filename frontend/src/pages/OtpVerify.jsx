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
          <div className="card-badge">
            <div className="badge-dot" />
            <span className="badge-label">Email Verification</span>
          </div>
          <h2>Verify Your Email</h2>
          <p className="auth-info">
            We sent a 6-digit code to: <strong>{email}</strong>
          </p>

          {error && <div className="auth-error">{error}</div>}
          {success && <div className="auth-success">{success}</div>}

          <form onSubmit={handleVerify}>
            <div className="field">
              <label>6-Digit Code</label>
              <input
                type="text"
                className="otp-input"
                inputMode="numeric"
                pattern="\d{6}"
                maxLength={6}
                placeholder="######"
                required
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              />
            </div>

            <button type="submit" className="btn-auth" disabled={loading || code.length !== 6}>
              {loading ? 'Verifying...' : 'Verify'}
            </button>

            <div className="btn-row">
              <button type="button" className="btn-secondary" onClick={handleResend}>
                Resend code
              </button>
