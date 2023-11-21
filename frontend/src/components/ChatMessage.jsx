import { memo } from 'react';
import formatMessage from '../utils/formatMessage';

function ChatMessage({ message, userName, lang }) {
  const sender = message.sender || message.role;
  const role = sender === 'user' ? 'user' : 'bot';
  const time = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString(lang === 'ar' ? 'ar-SA' : 'en-US', {
