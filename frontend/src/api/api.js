const API_BASE = '/api';

async function request(path, options = {}) {
  const token = localStorage.getItem('token');
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || body.message || `Request failed (${res.status})`);
  }

  return res.json();
}

export const auth = {
  login: (email, password) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) }),

  register: (name, email, password) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify({ name, email, password }) }),

  verifyOtp: (email, code) =>
    request('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ email, code }) }),

  resendOtp: (email) =>
    request('/auth/resend-otp', { method: 'POST', body: JSON.stringify({ email }) }),

  forgotPassword: (email) =>
    request('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ email }) }),

  resetPassword: (email, otp) =>
    request('/auth/reset-password', { method: 'POST', body: JSON.stringify({ email, otp }) }),

  me: () => request('/auth/me'),
};

export const chats = {
  list: (userId) =>
    request(`/users/${userId}/chats`),

  get: (chatId) =>
    request(`/chats/${chatId}`),

  create: (userId, title) =>
    request('/chats/', { method: 'POST', body: JSON.stringify({ user_id: userId, title }) }),

  sendMessage: (chatId, content) =>
    request(`/chats/${chatId}/message`, { method: 'POST', body: JSON.stringify({ content }) }),

  delete: (chatId, userId) =>
    request('/chats/delete', { method: 'POST', body: JSON.stringify({ chat_id: chatId, user_id: userId }) }),
};

export const users = {
  getProfile: (userId) =>
    request(`/users/${userId}`),
