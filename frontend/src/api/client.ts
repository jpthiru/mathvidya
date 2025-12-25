/**
 * API Client Configuration
 *
 * Axios instance configured for communicating with Mathvidya backend API.
 */

import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - Handle errors
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config;

    // Handle 401 - Unauthorized (token expired)
    if (error.response?.status === 401 && originalRequest) {
      // Clear token and redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }

    // Handle 403 - Forbidden
    if (error.response?.status === 403) {
      console.error('Access forbidden');
    }

    // Handle 429 - Rate limit exceeded
    if (error.response?.status === 429) {
      console.error('Rate limit exceeded. Please try again later.');
    }

    return Promise.reject(error);
  }
);

export default apiClient;
