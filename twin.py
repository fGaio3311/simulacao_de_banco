from collections import defaultdict
from datetime import datetime

class DigitalTwin:
    def __init__(self):
        self.users = defaultdict(lambda: {
            "saldo": 0,
            "ultimo_login": None,
            "total_depositado": 0,
            "total_pix_enviado": 0,
            "total_pix_recebido": 0,
            "n_logins": 0,
            "n_consultas_saldo": 0,
            "n_depositos": 0,
            "n_pix": 0,
            "pix_amounts_enviados": [],
            "pix_amounts_recebidos": [],
            "login_timestamps": [],
            "deposit_amounts": []
        })

    def apply_event(self, event):
        user = event.get("user")
        action = event.get("action")

        if not user or not action:
            return

        # Cria estado se não existir (já tratado pelo defaultdict)
        user_state = self.users[user]

        if action == "login":
            timestamp = event.get("timestamp", datetime.now().isoformat())
            user_state['ultimo_login'] = timestamp
            user_state['n_logins'] += 1
            user_state['login_timestamps'].append(timestamp)

        elif action == "balance":
            user_state['n_consultas_saldo'] += 1

        elif action == "deposit":
            amount = event.get("amount", 0)
            user_state['saldo'] += amount
            user_state['total_depositado'] += amount
            user_state['n_depositos'] += 1
            user_state['deposit_amounts'].append(amount)

        elif action == "pix":
            amount = event.get("amount", 0)
            to_user = event.get("to_user")

            # Atualiza remetente
            user_state['saldo'] -= amount
            user_state['total_pix_enviado'] += amount
            user_state['n_pix'] += 1
            user_state['pix_amounts_enviados'].append(amount)

            # Atualiza destinatário
            if to_user:
                recipient_state = self.users[to_user]
                recipient_state['saldo'] += amount
                recipient_state['total_pix_recebido'] += amount
                recipient_state['pix_amounts_recebidos'].append(amount)

    def summary(self):
        return {
            user: {
                "saldo": data["saldo"],
                "ultimo_login": data["ultimo_login"].isoformat() if data["ultimo_login"] else None,
                "n_logins": data["n_logins"],
                "n_consultas_saldo": data["n_consultas_saldo"],
                "total_depositado": data["total_depositado"],
                "n_depositos": data["n_depositos"],
                "total_pix_enviado": data["total_pix_enviado"],
                "total_pix_recebido": data["total_pix_recebido"],
                "n_pix": data["n_pix"],
            }
            for user, data in self.users.items()
        }

twin = DigitalTwin()