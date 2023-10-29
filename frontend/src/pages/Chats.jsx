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
      })
      .catch((err) => { if (!controller.signal.aborted) console.error(err); });
    return () => controller.abort();
  }, [activeId, scrollToBottom]);

  const activeChat = useMemo(() => chatList.find((c) => c.id === activeId), [chatList, activeId]);

  const handleCreate = async () => {
    const n = chatList.length + 1;
    const def = lang === 'ar' ? `\u0645\u062d\u0627\u062f\u062b\u0629 ${n}` : `Chat ${n}`;
    const title = await ui.prompt(t('advisor.chatName'), def);
    if (!title?.trim()) return;
    try {
      const data = await chatsApi.create(user.user_id, title.trim());
      setChatList((prev) => [{ id: data.id, title: title.trim(), message_count: 0 }, ...prev]);
      setActiveId(data.id);
      setMessages([]);
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id) => {
    if (!await ui.confirm(t('chats.confirmDeleteGeneric'))) return;
    try {
      await chatsApi.delete(id, user.user_id);
      setChatList((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) { setActiveId(null); setMessages([]); }
    } catch {
      await ui.alert(lang === 'ar' ? '\u0641\u0634\u0644 \u062d\u0630\u0641 \u0627\u0644\u0645\u062d\u0627\u062f\u062b\u0629' : 'Failed to delete conversation');
    }
  };

  const handleSend = async (content) => {
    let chatId = activeId;

    if (!chatId) {
      const n = chatList.length + 1;
      const def = lang === 'ar' ? `\u0645\u062d\u0627\u062f\u062b\u0629 ${n}` : `Chat ${n}`;
      try {
        const data = await chatsApi.create(user.user_id, def);
        chatId = data.id;
        setChatList((prev) => [{ id: data.id, title: def, message_count: 0 }, ...prev]);
        setActiveId(data.id);
      } catch { return; }
    }

    const userMsg = { sender: 'user', content, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setTyping(true);
    requestAnimationFrame(scrollToBottom);

    try {
      const data = await chatsApi.sendMessage(chatId, content);
      const botMsg = { sender: 'bot', content: data.content || t('advisor.noMessages'), timestamp: new Date().toISOString() };
      setMessages((prev) => [...prev, botMsg]);
      setChatList((prev) => prev.map((c) => (c.id === chatId ? { ...c, message_count: c.message_count + 2 } : c)));
    } catch {
      setMessages((prev) => [...prev, { sender: 'bot', content: t('advisor.errorConnection'), timestamp: new Date().toISOString() }]);
    } finally {
      setTyping(false);
      requestAnimationFrame(scrollToBottom);
    }
  };
