import { useState, useCallback } from 'react';
import axios from 'axios';

export function useTransactions() {
  const [error, setError] = useState(null);

  const deposit = useCallback(
    async (amount) => {
      setError(null);
      try {
        const token = localStorage.getItem('token');
        const resp = await axios.post(
          '/deposit',
          { amount },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        return resp.data.balance;       // retorna novo saldo
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
        throw err;
      }
    },
    []
  );

  const pix = useCallback(
    async (toUser, amount) => {
      setError(null);
      try {
        const token = localStorage.getItem('token');
        const resp = await axios.post(
          '/pix',
          { to_user: toUser, amount },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        return resp.data.balance;       // retorna novo saldo do remetente
      } catch (err) {
        setError(err.response?.data?.detail || err.message);
        throw err;
      }
    },
    []
  );

  return { deposit, pix, error };
}
