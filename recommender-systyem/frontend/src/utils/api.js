import axios from 'axios';

const api = axios.create({ baseURL: '/api' });

// Attach JWT token to every request
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

// ── AUTH ──────────────────────────────────────────────
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login:    (data) => api.post('/auth/login', data),
  me:       ()     => api.get('/auth/me'),
};

// ── PRODUCTS ──────────────────────────────────────────
export const productsAPI = {
  list:       (params) => api.get('/items/', { params }),
  get:        (id)     => api.get(`/items/${id}`),
  getByAsin:  (asin)   => api.get(`/items/asin/${asin}`),
};

// ── RATINGS ───────────────────────────────────────────
export const ratingsAPI = {
  submit:  (data) => api.post('/ratings/', data),
  myRatings: ()   => api.get('/ratings/my'),
};

// ── RECOMMENDATIONS ───────────────────────────────────
export const recsAPI = {
  similar:    (asin, params) => api.get(`/recommendations/similar/${asin}`, { params }),
  forYou:     (params)       => api.get('/recommendations/for-you', { params }),
  trustCheck: (asin, params) => api.get(`/recommendations/trust-check/${asin}`, { params }),
  batchCheck: (data)         => api.post('/recommendations/batch-check', data),
};

// ── ANALYTICS ─────────────────────────────────────────
export const analyticsAPI = {
  overview:          () => api.get('/analytics/overview'),
  trustDistribution: () => api.get('/analytics/trust-distribution'),
  topTrusted:        () => api.get('/analytics/top-trusted'),
  categoryStats:     () => api.get('/analytics/category-stats'),
};

export default api;