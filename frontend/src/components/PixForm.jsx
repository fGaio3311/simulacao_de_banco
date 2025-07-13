import { useState } from "react";
import axios from "axios";

export default function PixForm() {
  const [toUser, setToUser] = useState("");
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState(null);

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const resp = await axios.post(
        "http://localhost:8000/pix",
        { to_user: toUser, amount: parseFloat(amount) },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setMessage(`Pix enviado! Novo saldo: R$ ${resp.data.balance.toFixed(2)}`);
      setToUser("");
      setAmount("");
    } catch (err) {
      setMessage(err.response?.data?.detail || "Erro no Pix.");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Enviar Pix</h2>
      <input
        type="text"
        placeholder="Para usuário"
        value={toUser}
        onChange={e => setToUser(e.target.value)}
        required
      />
      <input
        type="number"
        step="0.01"
        placeholder="Valor"
        value={amount}
        onChange={e => setAmount(e.target.value)}
        required
      />
      <button type="submit">Enviar Pix</button>
      {message && <p>{message}</p>}
    </form>
  );
}
