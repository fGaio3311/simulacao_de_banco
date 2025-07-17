// src/components/DepositForm.jsx
import { useState } from 'react'
import { deposit }  from '../api'

export default function DepositForm({ onDone }) {
  const [amt, setAmt]   = useState('')
  const [error, setError] = useState(null)

  async function handle(e) {
    e.preventDefault()
    try {
      await deposit(parseFloat(amt))
      setAmt('')
      onDone()
      setError(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro no depósito')
    }
  }

  return (
    <form onSubmit={handle}>
      <input
        placeholder="Valor"
        value={amt}
        onChange={e => setAmt(e.target.value)}
      />
      <button>Depósito</button>
      {error && <p style={{color:'red'}}>{error}</p>}
    </form>
  )
}
