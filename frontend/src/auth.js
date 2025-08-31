import { jwtDecode } from 'jwt-decode'

export function setToken(token) {
  if (token) {
    localStorage.setItem('dexter_token', token)
  } else {
    localStorage.removeItem('dexter_token')
  }
}

export function getToken() {
  return localStorage.getItem('dexter_token')
}

export function isAuthed() {
  return !!getToken()
}

export function userInfo() {
  const token = getToken()
  if (!token) return null
  try {
    return jwtDecode(token)
  } catch {
    return null
  }
}
