import axios from 'axios';

const apiprivate = axios.create({
  baseURL: '/api/',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' }
});

// Attach access token from cookie as Authorization header
apiprivate.interceptors.request.use(config => {
  if (typeof document !== 'undefined') {
    const token = document.cookie.match(/(?:^|; )token=([^;]+)/)?.[1];
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default apiprivate;
