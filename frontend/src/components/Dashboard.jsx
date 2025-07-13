import { useEffect, useState } from 'react';
import axios from 'axios';
import DepositForm from './DepositForm';
import PixForm     from './PixForm';

export default function Dashboard() {
  const [balance,    setBalance]    = useState(0);
  const [twinSummary, setTwinSummary] = useState({});

  const token = localStorage.getItem('token');

  const fetchBalance = async () => {
    const resp = await axios.get('/balance', {
      headers: { Authorization: `Bearer ${token}` }
    });
    setBalance(resp.data.balance);
  };

  const fetchTwin = async () => {
    const resp = await axios.get('/digital-twin/summary');
    setTwinSummary(resp.data);
  };

  const onSuccess = async () => {
    await fetchBalance();
    await fetchTwin();
  };

  useEffect(() => {
    fetchBalance();
    fetchTwin();
  }, []);

  return (
    <div>
      <h1>Saldo: R$ {balance.toFixed(2)}</h1>

      <div style={{ display: 'flex', gap: 24 }}>
        <DepositForm onSuccess={onSuccess} />
        <PixForm     onSuccess={onSuccess} />
      </div>

      <section>
        <h2>Resumo Digital Twin</h2>
        <pre>{JSON.stringify(twinSummary, null, 2)}</pre>
      </section>
    </div>
  );
}
