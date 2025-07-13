import { useState } from 'react';
import axios from 'axios';

export default function LoginForm({ onLogin }) {
  const [user,  setUser]  = useState('');
  const [pass,  setPass]  = useState('');
  const [err,   setErr]   = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async e => {
    e.preventDefault();
    setLoading(true);
    try {
      const resp = await axios.post(
        '/token',
        `username=${encodeURIComponent(user)}&password=${encodeURIComponent(pass)}`,
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );
      localStorage.setItem('token', resp.data.access_token);
      onLogin(resp.data.access_token);
    } catch (e) {
      setErr(e.response?.data?.detail || e.message);
    }
    setLoading(false);
  };

  return (
    <form onSubmit={submit}>
      <h2>Entrar</h2>
      <input
        value={user}
        onChange={e => setUser(e.target.value)}
        placeholder="Usuário"
        required
      />
      <input
        type="password"
        value={pass}
        onChange={e => setPass(e.target.value)}
        placeholder="Senha"
        required
      />
      <button disabled={loading}>{loading ? '…' : 'Entrar'}</button>
      {err && <p className="error">{err}</p>}
    </form>
  );
}
