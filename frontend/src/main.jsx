import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { I18nProvider } from './context/I18nContext';
import { UIProvider } from './components/UIModal';
import ErrorBoundary from './components/ErrorBoundary';
import App from './App';
