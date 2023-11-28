import DOMPurify from 'dompurify';

export default function formatMessage(text) {
  if (!text) return '';

  text = text.replace(/\s*\n\s*\.\s*$/gm, '.').replace(/\s*\n\s*\.\s*\n/gm, '.\n');

  if (text.includes('<table') || text.includes('<tr') || text.includes('<td')) {
