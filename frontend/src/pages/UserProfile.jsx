import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { useUI } from '../components/UIModal';
import { users } from '../api/api';
import '../styles/profile.css';

const PALETTE = ['#7c3aed', '#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

function getInitials(name, email) {
  const n = (name || '').trim();
  if (n) {
    const parts = n.split(/\s+/);
    return parts.slice(0, 2).map((p) => p.charAt(0).toUpperCase()).join('');
  }
  return (email || '').slice(0, 2).toUpperCase();
}

export default function UserProfile() {
  const { user, logout } = useAuth();
  const { t, lang } = useI18n();
  const ui = useUI();
  const navigate = useNavigate();

  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState({ text: '', type: '' });
  const [copied, setCopied] = useState(false);
