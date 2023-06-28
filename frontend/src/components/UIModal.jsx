import { createContext, useContext, useCallback, useState, useRef, useEffect } from 'react';
import { useI18n } from '../context/I18nContext';

const UIContext = createContext(null);

export function UIProvider({ children }) {
  const { lang } = useI18n();
  const [modal, setModal] = useState(null);
  const resolveRef = useRef(null);
  const inputRef = useRef(null);
