// src/App.js
import { useState } from 'react'
import LoginForm  from './components/LoginForm'
import Dashboard  from './components/Dashboard'

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token'))

  return token
    ? <Dashboard />
    : <LoginForm onLogin={setToken} />
}
