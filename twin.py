from collections import defaultdict
from datetime import datetime
from typing import Dict


class DigitalTwin:
    def __init__(self):
        # Estado agregado por usuário
        self.users = defaultdict(lambda: {
            "saldo": 0.0,
            "n_logins": 0,
            "n_saldo": 0,
            "n_depositos": 0,
            "n_pix": 0,
            "total_depositado": 0.0,
            "total_pix_enviado": 0.0,
            "total_pix_recebido": 0.0,
            "eventos": [],  # eventos brutos
            "login_times": [],
            "pix_valores": [],
        })

    def apply_event(self, event: Dict):
        tipo = event.get("tipo")
        info = event.get("info", {})
        user = info.get("user")
        timestamp = event.get("timestamp", datetime.utcnow().isoformat())

        if not user or not tipo:
            return

        u = self.users[user]
        u["eventos"].append(event)  # guarda evento completo (shadow)

        if tipo == "login":
            u["n_logins"] += 1
            u["login_times"].append(timestamp)

        elif tipo == "balance":
            u["n_saldo"] += 1

        elif tipo == "deposit":
            valor = info.get("amount", 0.0)
            u["n_depositos"] += 1
            u["total_depositado"] += valor
            u["saldo"] += valor

        elif tipo == "pix":
            valor = info.get("amount", 0.0)
            to_user = info.get("to_user")
            u["n_pix"] += 1
            u["total_pix_enviado"] += valor
            u["saldo"] -= valor
            u["pix_valores"].append(valor)

            # atualizar destinatário
            if to_user:
                r = self.users[to_user]
                r["total_pix_recebido"] += valor
                r["saldo"] += valor
                r["pix_valores"].append(valor)

    def summary(self):
        return {
            user: {
                "saldo": data["saldo"],
                "n_logins": data["n_logins"],
                "n_saldo": data["n_saldo"],
                "n_depositos": data["n_depositos"],
                "n_pix": data["n_pix"],
                "total_depositado": data["total_depositado"],
                "total_pix_enviado": data["total_pix_enviado"],
                "total_pix_recebido": data["total_pix_recebido"],
            }
            for user, data in self.users.items()
        }

    def get_shadow(self, username: str):
        user = self.users.get(username)
        if not user:
            return {"erro": "Usuário não encontrado"}
        return {
            "eventos": user["eventos"][-20:],  # últimos 20 eventos
            "saldo": user["saldo"],
        }

    def stats(self):
        tipos = defaultdict(int)
        for user_data in self.users.values():
            for ev in user_data["eventos"]:
                tipos[ev["tipo"]] += 1
        return tipos

    def sazonalidade(self):
        horarios = defaultdict(int)
        for user_data in self.users.values():
            for ev in user_data["eventos"]:
                try:
                    hora = datetime.fromisoformat(ev["timestamp"]).hour
                    horarios[hora] += 1
                except Exception as e:
                    print(f"Houve uma exceção do tipo: {type(e).__name__}")
                    print(f"Detalhes da exceção: {e}")
                    continue
        return dict(sorted(horarios.items()))


twin = DigitalTwin()
