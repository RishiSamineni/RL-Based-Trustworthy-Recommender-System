import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api'
});

api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token');
  if (token) {
    cfg.headers.Authorization = `Bearer ${token}`;
  }
  return cfg;
});

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
};

export const productsAPI = {
  list: (params) => api.get('/items/', { params }),
  get: (id) => api.get(`/items/${id}`),
};

export const recsAPI = {
  forYou: () => api.get('/items/'),
  getTrust: (asin) => api.get(`/recommendations/trust-check/${asin}`),
  getSimilar: (asin, limit = 6, threshold = 0.3) =>
    api.get(`/recommendations/similar/${asin}`, {
      params: { limit, threshold }
    }),
};

export default api;