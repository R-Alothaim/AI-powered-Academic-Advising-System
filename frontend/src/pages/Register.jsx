import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AuthBackground from '../components/AuthBackground';
import '../styles/auth-bg.css';

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rePassword, setRePassword] = useState('');
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const errs = [];
    if (!name.trim()) errs.push('Full name is required');
    if (!email.includes('@university.edu.sa')) errs.push('Only @university.edu.sa emails are allowed');
    if (password.length < 8) errs.push('Password must be at least 8 characters');
    if (!/[A-Z]/.test(password)) errs.push('Password must contain an uppercase letter');
    if (!/[a-z]/.test(password)) errs.push('Password must contain a lowercase letter');
    if (!/\d/.test(password)) errs.push('Password must contain a digit');
    if (!/[^A-Za-z0-9]/.test(password)) errs.push('Password must contain a special character');
    if (password !== rePassword) errs.push('Passwords do not match');
    return errs;
  };
