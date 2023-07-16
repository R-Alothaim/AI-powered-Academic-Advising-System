import { createContext, useContext, useState, useCallback, useEffect, useMemo } from 'react';
import en from '../locales/en.json';
import ar from '../locales/ar.json';

const locales = { en, ar };

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLangState] = useState(() => localStorage.getItem('neon-lang') || 'ar');

  const dir = lang === 'ar' ? 'rtl' : 'ltr';

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dir;
    document.body.classList.toggle('rtl', lang === 'ar');
  }, [lang, dir]);

  const setLang = useCallback((newLang) => {
    const l = newLang === 'en' ? 'en' : 'ar';
    localStorage.setItem('neon-lang', l);
    setLangState(l);
  }, []);

  const t = useCallback((key, fallback) => {
    return locales[lang]?.[key] || fallback || key;
  }, [lang]);

  const value = useMemo(() => ({ lang, dir, setLang, t }), [lang, dir, setLang, t]);

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  );
}
