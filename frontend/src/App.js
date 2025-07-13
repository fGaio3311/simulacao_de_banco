import { useState } from 'react';
import LoginForm from './components/LoginForm';
import Dashboard  from './components/Dashboard';

export default function App() {
  // guarda o token no estado pra re-render
  const [token, setToken] = useState(localStorage.getItem('token'));

  if (!token) {
    // ainda não logado
    return <LoginForm onLogin={setToken} />;
  }

  return <Dashboard />;
}
