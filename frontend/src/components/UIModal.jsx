import { createContext, useContext, useCallback, useState, useRef, useEffect } from 'react';
import { useI18n } from '../context/I18nContext';

const UIContext = createContext(null);

export function UIProvider({ children }) {
  const { lang } = useI18n();
  const [modal, setModal] = useState(null);
  const resolveRef = useRef(null);
  const inputRef = useRef(null);

  const close = useCallback((value) => {
    if (resolveRef.current) resolveRef.current(value);
    resolveRef.current = null;
    setModal(null);
  }, []);

  const alert = useCallback((message) => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setModal({ message, type: 'alert' });
    });
  }, []);

  const confirm = useCallback((message) => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setModal({ message, type: 'confirm' });
    });
  }, []);

  const prompt = useCallback((message, defaultValue = '') => {
    return new Promise((resolve) => {
      resolveRef.current = resolve;
      setModal({ message, type: 'prompt', defaultValue });
    });
  }, []);

  useEffect(() => {
    if (modal?.type === 'prompt' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [modal]);

  const isAr = lang === 'ar';

  return (
    <UIContext.Provider value={{ alert, confirm, prompt }}>
      {children}

      {modal && (
        <div
          style={{
            position: 'fixed', inset: 0, background: 'rgba(8,15,39,0.7)',
            backdropFilter: 'blur(8px)', zIndex: 9999,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            animation: 'fadeIn 0.2s ease',
          }}
          onClick={() => modal.type === 'alert' ? close(true) : close(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: 'rgba(13,30,58,0.95)', border: '1px solid rgba(255,255,255,0.12)',
              padding: 24, borderRadius: 20,
              width: '90%', maxWidth: 400, boxShadow: '0 30px 80px rgba(0,0,0,0.5)',
              display: 'flex', flexDirection: 'column', gap: 16,
              backdropFilter: 'blur(28px)',
            }}
          >
            <div style={{ fontSize: 16, color: 'rgba(220,230,255,0.9)', lineHeight: 1.5 }}>
              {modal.message}
            </div>
