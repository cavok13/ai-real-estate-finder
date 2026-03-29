import axios from 'axios';

const API_URL = 'https://ai-real-estate-finder.onrender.com/api/v1';

console.log('API URL:', API_URL);

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  console.log('API Request:', config.method?.toUpperCase(), config.url);
  return config;
});

api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Error:', error.message, error.config?.url);
    if (error.response) {
      console.error('Error Status:', error.response.status);
      console.error('Error Data:', error.response.data);
    }
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
      }
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: (email: string, password: string) => {
    console.log('Logging in:', email);
    return api.post('/auth/login', { email, password });
  },
  register: (data: { email: string; password: string; full_name?: string; referral_code?: string }) => {
    console.log('Registering:', data.email);
    return api.post('/auth/register', data);
  },
  getMe: () => api.get('/auth/me'),
};

export const propertiesAPI = {
  getAll: (params?: { city?: string; page?: number; per_page?: number }) =>
    api.get('/properties', { params }),
  getBestDeals: (city?: string, limit?: number) =>
    api.get('/properties/best-deals', { params: { city, limit } }),
  getById: (id: number) => api.get(`/properties/${id}`),
  analyze: (propertyId: number) => api.get(`/properties/${propertyId}/analyze`),
};

export const analysisAPI = {
  create: (data: { budget_min?: number; budget_max?: number; preferred_city?: string; property_type?: string; bedrooms_min?: number }) =>
    api.post('/analyze', data),
  getHistory: (page?: number) => api.get('/analyze/history', { params: { page } }),
  getStats: () => api.get('/analyze/stats'),
};

export const paymentsAPI = {
  getPackages: () => api.get('/payments/packages'),
  createCheckout: (packageId: string, successUrl: string, cancelUrl: string) =>
    api.post('/payments/create-checkout', { package_id: packageId, success_url: successUrl, cancel_url: cancelUrl }),
  getTransactions: () => api.get('/payments/transactions'),
};

export const marketsAPI = {
  // UAE Market Data
  getUAEAreas: (market: 'dubai' | 'abu_dhabi' = 'dubai', sortBy: 'yield' | 'price' | 'transactions' = 'yield') =>
    api.get('/markets/uae/areas', { params: { market, sort_by: sortBy } }),
  getAreaDetails: (areaName: string) =>
    api.get(`/markets/uae/areas/${areaName}`),
  getBestROI: (market: 'dubai' | 'abu_dhabi' = 'dubai', limit: number = 5) =>
    api.get('/markets/uae/best-roi', { params: { market, limit } }),
  getBestDeals: (market: 'dubai' | 'abu_dhabi' = 'dubai') =>
    api.get('/markets/uae/best-deals', { params: { market } }),
  getMarketSummary: (market: 'dubai' | 'abu_dhabi' = 'dubai') =>
    api.get('/markets/uae/summary', { params: { market } }),

  // Property Analysis
  analyzeURL: (url: string) =>
    api.post('/markets/analyze', { url }),
  analyzeURLFree: (url: string) =>
    api.post('/markets/analyze-free', { url }),
  analyzeBatch: (urls: string[]) =>
    api.post('/markets/analyze/batch', { urls }),

  // Credits
  getCredits: () => api.get('/markets/credits/balance'),
  getCreditPacks: () => api.get('/markets/credits/packs'),
  buyCredits: (creditPack: string) =>
    api.post('/markets/credits/buy', { credit_pack: creditPack }),

  // Plans
  getPlans: () => api.get('/markets/plans'),

  // Health
  health: () => api.get('/markets/health'),
};

export default api;
