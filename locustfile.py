from uuid import uuid4
from locust import HttpUser, task, between  # type: ignore[import]


class BankUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 1) registra um usuário novo e único
        username = f"user-{uuid4().hex[:8]}"
        self.client.post("/register", json={"username": username, "password": "pass"})

        # 2) faz login e armazena o token
        resp = self.client.post(
            "/token",
            data={"username": username, "password": "pass"}
        )
        token = resp.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {token}"}

        # 3) garante que esse usuário tenha saldo suficiente para o pix
        self.client.post("/deposit", headers=self.headers, json={"amount": 100})

    @task(3)
    def view_balance(self):
        self.client.get("/balance", headers=self.headers)

    @task(2)
    def deposit(self):
        self.client.post("/deposit", headers=self.headers, json={"amount": 10})

    @task(1)
    def pix(self):
        # envia para um segundo usuário pré-criado (fora do Locust)
        self.client.post("/pix", headers=self.headers,
                         json={"to_user": "user2", "amount": 5})
