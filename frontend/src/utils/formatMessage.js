import DOMPurify from 'dompurify';

export default function formatMessage(text) {
  if (!text) return '';

  text = text.replace(/\s*\n\s*\.\s*$/gm, '.').replace(/\s*\n\s*\.\s*\n/gm, '.\n');

  if (text.includes('<table') || text.includes('<tr') || text.includes('<td')) {
    text = text
      .replace(/>\s+</g, '><')
      .replace(/(<table[^>]*>)/g, '<div style="margin:12px 0">$1')
      .replace(/(<\/table>)/g, '$1</div>');
    return DOMPurify.sanitize(text);
  }

  text = text.replace(/^\* (.+)$/gm, '<li>$1</li>').replace(/^- (.+)$/gm, '<li>$1</li>');
  text = text.replace(/(<li>.*<\/li>\s*)+/gs, (m) => '<ul>' + m + '</ul>');
