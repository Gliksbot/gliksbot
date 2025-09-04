import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8080'
export const api = axios.create({ baseURL: apiBase })

api.interceptors.request.use((cfg) => {
  const token = localStorage.getItem('dexter_token')
  if (token) {
    cfg.headers.Authorization = `Bearer ${token}`
  }
  return cfg
})
