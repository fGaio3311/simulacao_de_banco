// src/components/PixForm.jsx
import { useState } from 'react'
import { pix }         from '../api'

export default function PixForm({ onDone }) {
  const [toUser, setToUser] = useState('')
  const [amt, setAmt]       = useState('')
  const [error, setError]   = useState(null)

  async function handle(e) {
    e.preventDefault()
    try {
      await pix(toUser, parseFloat(amt))
      setToUser('')
      setAmt('')
      onDone()
      setError(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro no PIX')
    }
  }

  return (
    <form onSubmit={handle}>
      <input
        placeholder="Para usuário"
        value={toUser}
        onChange={e => setToUser(e.target.value)}
      />
      <input
        placeholder="Valor"
        value={amt}
        onChange={e => setAmt(e.target.value)}
      />
      <button>PIX</button>
      {error && <p style={{color:'red'}}>{error}</p>}
    </form>
  )
}
