import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useAuth } from '../context/AuthContext';
import { useI18n } from '../context/I18nContext';
import { useUI } from '../components/UIModal';
import { chats as chatsApi } from '../api/api';
import ChatSidebar from '../components/ChatSidebar';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import '../styles/chat.css';

export default function Chats() {
  const { user } = useAuth();
  const { lang, t } = useI18n();
  const ui = useUI();

  const [chatList, setChatList] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [typing, setTyping] = useState(false);
  const [search, setSearch] = useState('');
  const [sidebarHidden, setSidebarHidden] = useState(false);

  const containerRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    const el = containerRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, []);

  useEffect(() => {
    if (!user) return;
    const controller = new AbortController();
    chatsApi.list(user.user_id)
      .then((data) => {
        if (!controller.signal.aborted) {
          setChatList(data.map((c) => ({ id: c.id, title: c.title, message_count: c.message_count || 0 })));
        }
      })
      .catch((err) => { if (!controller.signal.aborted) console.error(err); });
    return () => controller.abort();
  }, [user]);

  useEffect(() => {
    if (!activeId) { setMessages([]); return; }
    const controller = new AbortController();
    chatsApi.get(activeId)
      .then((data) => {
        if (!controller.signal.aborted) {
          setMessages(data.messages || []);
          requestAnimationFrame(scrollToBottom);
        }
