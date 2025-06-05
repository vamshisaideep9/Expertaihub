import axios from 'axios';

const apipublic = axios.create({
  baseURL: '/api/',
  withCredentials: false,
  headers: { 'Content-Type': 'application/json' }
});

export default apipublic;
