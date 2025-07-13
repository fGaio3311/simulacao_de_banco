import { useEffect, useState } from 'react';
import api from '../api';
import DepositForm from './DepositForm';
import PixForm     from './PixForm';

export default function Dashboard() {
  const [balance, setBalance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchBalance = async () => {
    try {
      const resp = await api.get('/balance');
      setBalance(resp.data.balance);
    } catch (err) {
      setError('Não foi possível carregar saldo');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalance();
  }, []);

  if (loading) return <p>Carregando...</p>;
  if (error) return <p className="error">{error}</p>;

  return (
    <div>
      <h1>Saldo: R$ {balance.toFixed(2)}</h1>

      <section>
        <h2>Fazer Depósito</h2>
        <DepositForm onSuccess={setBalance} />
      </section>

      <section>
        <h2>Fazer Pix</h2>
        <PixForm onSuccess={setBalance} />
      </section>
    </div>
  );
}
