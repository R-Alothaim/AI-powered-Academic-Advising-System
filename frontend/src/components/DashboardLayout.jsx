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

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const linkClass = ({ isActive }) =>
    `menu-item${isActive ? ' active' : ''}`;

  return (
    <>
      <aside className={`sidebar${sidebarVisible ? '' : ' hidden'}`}>
        <div className="dash-brand">
          <span className="logo">
            <svg viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg" width="20" height="20">
              <path
                d="M11 2L13.5 8H20L14.5 12L16.5 18L11 14L5.5 18L7.5 12L2 8H8.5L11 2Z"
                stroke="#EAD27A" strokeWidth="1.2" strokeLinejoin="round"
              />
            </svg>
          </span>
          <span className="dash-brand-text">{t('app.title', 'Academic Advisor')}</span>
        </div>

        <div className="lang-group" aria-label="Language">
          <div className="segmented" role="tablist">
            <button
              className={`seg-btn${lang === 'ar' ? ' active' : ''}`}
              onClick={() => setLang('ar')}
              role="tab"
              aria-selected={lang === 'ar'}
            >
              العربية
            </button>
            <button
              className={`seg-btn${lang === 'en' ? ' active' : ''}`}
              onClick={() => setLang('en')}
              role="tab"
              aria-selected={lang === 'en'}
            >
              English
            </button>
          </div>
        </div>
