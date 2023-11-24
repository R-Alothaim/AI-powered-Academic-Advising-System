import { useRef } from 'react';
import { useI18n } from '../context/I18nContext';

export default function ChatInput({ onSend, disabled }) {
  const { t } = useI18n();
  const textareaRef = useRef(null);

  const autosize = (el) => {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  const handleSend = () => {
    const val = textareaRef.current?.value.trim();
    if (!val) return;
    onSend(val);
    textareaRef.current.value = '';
    autosize(textareaRef.current);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
