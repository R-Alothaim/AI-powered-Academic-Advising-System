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
        </button>
      </div>
      <div className="search-row">
        <input
          className="chat-input"
          type="search"
          placeholder={t('advisor.search')}
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          aria-label={t('advisor.search')}
        />
      </div>
      <ul className="chat-list" role="listbox" aria-label={t('advisor.myChats')}>
        {filtered.length === 0 ? (
          <li style={{ padding: 20, textAlign: 'center', color: '#9ca3af', border: 'none', display: 'block' }}>
            {t('advisor.noChats')}
          </li>
        ) : (
          filtered.map((c) => (
            <li
              key={c.id}
              className={c.id === activeId ? 'active' : ''}
              onClick={() => onSelect(c.id)}
              role="option"
              aria-selected={c.id === activeId}
            >
              <div>
                <div className="title">{c.title}</div>
                <div className="meta">
                  <span className="msg-badge">
                    {c.message_count}{' '}
                    {lang === 'ar' ? '\u0631\u0633\u0627\u0644\u0629' : c.message_count === 1 ? 'message' : 'messages'}
                  </span>
                </div>
              </div>
              <button
                className="delete-chat"
                onClick={(e) => { e.stopPropagation(); onDelete(c.id); }}
                title={t('actions.delete')}
                aria-label={`${t('actions.delete')} ${c.title}`}
              >
                ×
              </button>
            </li>
          ))
        )}
      </ul>
    </aside>
  );
