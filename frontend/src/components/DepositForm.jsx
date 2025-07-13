import { useState } from "react";
import axios from "axios";

export default function DepositForm() {
  const [amount, setAmount] = useState("");
  const [message, setMessage] = useState(null);

  const handleSubmit = async e => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("token");
      const resp = await axios.post(
        "http://localhost:8000/deposit",
        { amount: parseFloat(amount) },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setMessage(`Saldo atual: R$ ${resp.data.balance.toFixed(2)}`);
      setAmount("");
    } catch (err) {
      setMessage(err.response?.data?.detail || "Erro no depósito.");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Depósito</h2>
      <input
        type="number"
        step="0.01"
        placeholder="Valor"
        value={amount}
        onChange={e => setAmount(e.target.value)}
        required
      />
      <button type="submit">Depositar</button>
      {message && <p>{message}</p>}
    </form>
  );
}
