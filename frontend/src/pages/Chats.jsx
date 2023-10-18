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
