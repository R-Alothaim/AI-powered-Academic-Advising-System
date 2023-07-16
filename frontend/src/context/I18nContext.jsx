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
