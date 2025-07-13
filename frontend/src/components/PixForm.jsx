import { useState } from 'react';
import api from '../api';

export default function PixForm({ onSuccess }) {
  const [toUser, setToUser] = useState('');
  const [amount, setAmount] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = async e => {
    e.preventDefault();
    setError(null);
    try {
      const resp = await api.post('/pix', {
        to_user: toUser,
        amount: Number(amount),
      });
      onSuccess(resp.data.balance);
      setToUser('');
      setAmount('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Erro no Pix');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        Destinatário:
        <input
          type="text"
          value={toUser}
          onChange={e => setToUser(e.target.value)}
          required
        />
      </label>
      <label>
        Valor:
        <input
          type="number"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          min="1"
          required
        />
      </label>
      <button type="submit">Enviar Pix</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}
