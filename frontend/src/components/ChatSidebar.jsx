import { memo } from 'react';
import { useI18n } from '../context/I18nContext';

function ChatSidebar({ chats, activeId, search, onSearch, onSelect, onDelete, onCreate }) {
  const { lang, t } = useI18n();

  const filtered = chats.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()),
  );
