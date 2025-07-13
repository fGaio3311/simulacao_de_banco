import { useState } from 'react';
import api from '../api';

export default function DepositForm({ onSuccess }) {
  const [amount, setAmount] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = async e => {
    e.preventDefault();
    setError(null);
    try {
      const resp = await api.post('/deposit', { amount: Number(amount) });
      onSuccess(resp.data.balance);
      setAmount('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro no depósito');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Valor para depositar:
        <input
          type="number"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          min="1"
          required
        />
      </label>
      <button type="submit">Depositar</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
