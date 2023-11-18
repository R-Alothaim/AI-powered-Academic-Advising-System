import { memo } from 'react';
import { useI18n } from '../context/I18nContext';

function ChatSidebar({ chats, activeId, search, onSearch, onSelect, onDelete, onCreate }) {
  const { lang, t } = useI18n();

  const filtered = chats.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <aside className="chat-side" aria-label="Conversations">
      <div className="side-head">
        <h3>{t('advisor.myChats')}</h3>
        <button className="chat-btn icon-only" onClick={onCreate} title={t('advisor.newChat')}>
          <span className="glow" />
          <span>+</span>
