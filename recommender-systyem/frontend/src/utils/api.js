import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api'
});

// Attach JWT token
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) {
    cfg.headers.Authorization = `Bearer ${token}`;
  }
  return cfg;
});


// ───────── AUTH ─────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};


// ───────── PRODUCTS ─────────
export const productsAPI = {
  list: (params) => api.get('/items/', { params }),
  get: (asin) => api.get(`/items/${asin}`),
};


// ───────── RECOMMENDATIONS ─────────
export const recsAPI = {

  // 🔥 Correct endpoint
  forYou: () =>
    api.get('/recommendations/for-you'),

  // 🔥 Trust check (used in ProductDetail)
  getTrust: (asin) =>
    api.get(`/recommendations/trust-check/${asin}`),

  // 🔥 IMPORTANT: match backend params
  getSimilar: (asin, top_n = 6, min_trust = 0.3) =>
    api.get(`/recommendations/similar/${asin}`, {
      params: { top_n, min_trust }
    }),
};

export default api;