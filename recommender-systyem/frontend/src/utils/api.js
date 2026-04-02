import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000' // 🔥 important
});

// Attach JWT token
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// ── AUTH ─────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

// ── PRODUCTS ─────────────────────
export const productsAPI = {
  list: (params) => api.get('/items/', { params }),
  get: (id) => api.get(`/items/${id}`),
};

// ── RECOMMENDATIONS ──────────────
export const recsAPI = {
  // 🔥 FIXED
  similar: (asin, top_n = 10, min_trust = 0) =>
    api.get(`/recommendations/similar/${asin}`, {
      params: { top_n, min_trust }
    }),

  forYou: () =>
    api.get('/recommendations/for-you'),

  trustCheck: (asin) =>
    api.get(`/recommendations/trust-check/${asin}`),
};

export default api;