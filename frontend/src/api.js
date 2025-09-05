import axios from 'axios'

const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8080'
export const api = axios.create({ baseURL: apiBase })
