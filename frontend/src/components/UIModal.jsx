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

            {modal.type === 'prompt' && (
              <input
                ref={inputRef}
                type="text"
                defaultValue={modal.defaultValue}
                onKeyDown={(e) => { if (e.key === 'Enter') close(inputRef.current.value); }}
                style={{
                  width: '100%', padding: 12, border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: 10, outline: 'none', background: 'rgba(255,255,255,0.06)',
                  color: 'rgba(220,230,255,0.9)', fontSize: 14, fontFamily: 'Inter, sans-serif',
                }}
              />
            )}

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 8 }}>
              {modal.type !== 'alert' && (
                <button
                  onClick={() => close(false)}
                  style={{
                    padding: '10px 18px', borderRadius: 10, cursor: 'pointer',
                    background: 'rgba(255,255,255,0.06)', color: 'rgba(160,190,255,0.8)',
                    border: '1px solid rgba(255,255,255,0.15)', fontFamily: 'Inter, sans-serif', fontSize: 14,
                  }}
                >
                  {isAr ? '\u0625\u0644\u063a\u0627\u0621' : 'Cancel'}
                </button>
              )}
              <button
                onClick={() => {
                  if (modal.type === 'prompt') close(inputRef.current?.value ?? '');
                  else close(true);
                }}
                style={{
                  padding: '10px 18px', borderRadius: 10, cursor: 'pointer',
                  background: 'linear-gradient(135deg,#2458D4,#1A3EA8)', color: '#fff',
                  border: 'none', boxShadow: '0 4px 24px rgba(36,88,212,.35)',
                  fontFamily: 'Inter, sans-serif', fontWeight: 500, fontSize: 14,
                }}
              >
                {isAr ? '\u0645\u0648\u0627\u0641\u0642' : 'OK'}
              </button>
            </div>
          </div>
        </div>
      )}
    </UIContext.Provider>
  );
}

export function useUI() {
  const ctx = useContext(UIContext);
  if (!ctx) throw new Error('useUI must be used within UIProvider');
  return ctx;
}
