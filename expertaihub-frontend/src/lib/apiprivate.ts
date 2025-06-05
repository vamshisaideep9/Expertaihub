import axios from 'axios';

const apiprivate = axios.create({
  baseURL: '/api/',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' }
});

export default apiprivate;
