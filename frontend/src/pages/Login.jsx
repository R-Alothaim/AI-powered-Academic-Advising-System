import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthBackground from '../components/AuthBackground';
import '../styles/auth-bg.css';

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const next = location.state?.from?.pathname || '/dashboard/chats';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrors([]);
    setLoading(true);

    try {
      const data = await login(email, password);

      if (data.requires_verification) {
        navigate('/otp-verify', { state: { email } });
        return;
      }

      navigate(next, { replace: true });
    } catch (err) {
      setErrors([err.message]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <AuthBackground />

      <div className="card-wrap">
        <div className="auth-card">
          <div className="card-badge">
            <div className="badge-dot" />
            <span className="badge-label">Secure University Portal</span>
          </div>
          <h2>Sign In</h2>
          <p className="sub">* Only @university.edu.sa emails are allowed</p>

          {errors.length > 0 && (
            <div className="auth-error">
              {errors.map((err, i) => (
                <p key={i}>{err}</p>
              ))}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div className="field">
              <label>Email Address</label>
              <input
                type="email"
                placeholder="Your Email (@university.edu.sa)"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
              />
            </div>

            <div className="field">
              <label>Password</label>
              <input
                type="password"
                placeholder="••••••••"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
              />
            </div>

            <button type="submit" className="btn-auth" disabled={loading}>
              {loading ? 'Signing in...' : 'Login'}
            </button>

            <div className="card-links">
              <Link to="/register" state={{ next }}>
                Create an account
              </Link>
