import { useRef } from 'react';
import { useI18n } from '../context/I18nContext';

export default function ChatInput({ onSend, disabled }) {
  const { t } = useI18n();
  const textareaRef = useRef(null);

  const autosize = (el) => {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };
