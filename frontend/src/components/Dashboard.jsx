// src/components/Dashboard.jsx
import { useEffect, useState } from 'react'
import { getBalance } from '../api'
import DepositForm from './DepositForm'
import PixForm     from './PixForm'

export default function Dashboard() {
  const [saldo, setSaldo] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    load()
  }, [])

  async function load() {
    try {
      const b = await getBalance()
      setSaldo(b)
      setError(null)
    } catch (err) {
      setError('Não foi possível carregar saldo')
    }
  }

  if (error) {
    return <p>{error}</p>
  }
  if (saldo === null) {
    return <p>Carregando...</p>
  }

  return (
    <div>
      <h1>Saldo: R$ {saldo.toFixed(2)}</h1>
      <DepositForm onDone={load} />
      <PixForm onDone={load} />
    </div>
  )
}
