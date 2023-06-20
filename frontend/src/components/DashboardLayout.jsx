import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import '../styles/dashboard.css';

export default function DashboardLayout() {
  const { logout } = useAuth();
  const { lang, setLang, t } = useI18n();
  const navigate = useNavigate();
  const [sidebarVisible, setSidebarVisible] = useState(true);
