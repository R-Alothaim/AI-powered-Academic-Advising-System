import { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/DashboardLayout';
import ProtectedRoute from './components/ProtectedRoute';

const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const OtpVerify = lazy(() => import('./pages/OtpVerify'));
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'));
const ForgotPasswordVerify = lazy(() => import('./pages/ForgotPasswordVerify'));
const Chats = lazy(() => import('./pages/Chats'));
const UserProfile = lazy(() => import('./pages/UserProfile'));
const Calendar = lazy(() => import('./pages/Calendar'));
const NotFound = lazy(() => import('./pages/NotFound'));

function PageLoader() {
  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: '#0A1628', color: 'rgba(160,190,255,0.6)', fontFamily: 'Inter, sans-serif',
    }}>
      Loading...
    </div>
  );
}
