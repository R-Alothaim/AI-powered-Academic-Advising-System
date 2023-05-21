import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { auth } from '../api/api';
import AuthBackground from '../components/AuthBackground';
import '../styles/auth-bg.css';

export default function ForgotPasswordVerify() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';

  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await auth.resetPassword(email, otp);
      navigate('/login', {
        replace: true,
        state: { message: 'A temporary password has been sent to your email.' },
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
