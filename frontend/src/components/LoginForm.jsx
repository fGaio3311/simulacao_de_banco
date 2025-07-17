// src/components/LoginForm.jsx
import { useState } from 'react'
import axios from 'axios'

export default function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async e => {
    e.preventDefault()

    try {
      // monta o body como form-urlencoded
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)

      const res = await axios.post(
        'http://localhost:8000/token',
        params,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      )

      const token = res.data.access_token
      localStorage.setItem('token', token)
      onLogin(token)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro ao logar')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Entrar</h1>
      <input
        placeholder="Usuário"
        value={username}
        onChange={e => setUsername(e.target.value)}
      />
      <input
        placeholder="Senha"
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
      />
      <button type="submit">Entrar</button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </form>
  )
}
