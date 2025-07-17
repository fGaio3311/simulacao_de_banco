// src/api.js
import axios from 'axios'

// cria a instância apontando para a sua API
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,  // ex: http://localhost:8000
})

// injeta o token em todas as requisições
api.interceptors.request.use(cfg => {
  const t = localStorage.getItem('token')
  if (t) cfg.headers.Authorization = `Bearer ${t}`
  return cfg
})

// faz o login e guarda o token no localStorage
export async function login(username, password) {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  // OBS: OAuth2PasswordRequestForm espera form-url-encoded
  const { data } = await api.post('/token', params)
  localStorage.setItem('token', data.access_token)
  return data
}

// registra novo usuário
export async function register(username, password) {
  const { data } = await api.post('/register', { username, password })
  return data
}

// busca o saldo do usuário logado
export async function getBalance() {
  const { data } = await api.get('/balance')
  return data.balance
}

// faz depósito e retorna o novo saldo
export async function deposit(amount) {
  const { data } = await api.post('/deposit', { amount })
  return data.balance
}

// faz pix e retorna o novo saldo
export async function pix(to_user, amount) {
  const { data } = await api.post('/pix', { to_user, amount })
  return data.balance
}

export default api
