# tests/test_api.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# importe seu app e suas definições de modelo/db
from main import app, Base, get_db
from models import User, Transaction, Log  # ajuste os nomes conforme seu projeto

# --- Fixture de banco de teste (SQLite em memória) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Cria todas as tabelas
Base.metadata.create_all(bind=engine)

# Override do get_db
@pytest.fixture(scope="module")
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

# --- Testes de Funcionalidades Básicas ---

def test_register_and_login(client):
    # Registro
    resp = client.post("/register", json={"username": "alice", "password": "senha123"})
    assert resp.status_code == 200
    assert resp.json()["message"] == "User created"

    # Login
    resp = client.post("/login", json={"username": "alice", "password": "senha123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_balance_deposit_and_pix_and_logs(client):
    # Gera token de alice
    token = client.post("/login", json={"username": "alice", "password": "senha123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Consulta saldo inicial (deve ser 0)
    resp = client.get("/balance", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["balance"] == 0

    # Depósito de 100
    resp = client.post("/deposit", headers=headers, json={"amount": 100})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 100

    # Transferência Pix para bob
    client.post("/register", json={"username": "bob", "password": "senha456"})
    resp = client.post("/pix", headers=headers, json={"to_user": "bob", "amount": 30})
    assert resp.status_code == 200
    assert resp.json()["balance"] == 70

    # Consulta logs
    resp = client.get("/logs", headers=headers)
    assert resp.status_code == 200
    logs = resp.json()
    # Devem existir 4 ações: login, saldo, depósito, pix
    assert len(logs) >= 4
    actions = [l["action"] for l in logs]
    assert "login" in actions
    assert "balance" in actions
    assert "deposit" in actions
    assert "pix" in actions

# --- Testes de Vulnerabilidade / Exploração ---

def test_sql_injection_login(client):
    # Tenta SQL Injection no login
    payload = {"username": "' OR 1=1 --", "password": "x"}
    resp = client.post("/login", json=payload)
    assert resp.status_code == 401  # deve rejeitar :contentReference[oaicite:0]{index=0}

def test_broken_authentication_bruteforce(client):
    # Simula vários logins inválidos sem bloqueio
    for _ in range(20):
        resp = client.post("/login", json={"username": "alice", "password": "wrong"})
        assert resp.status_code == 401
    # Não há bloqueio, logo continua retornando 401 sem 429 :contentReference[oaicite:1]{index=1}

def test_broken_object_level_authorization(client):
    # Alice tenta consultar saldo de Bob diretamente
    token_alice = client.post("/login", json={"username": "alice", "password": "senha123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token_alice}"}
    # Supondo endpoint /balance/{user_id}
    resp = client.get("/balance/2", headers=headers)
    assert resp.status_code in (401, 403)  # deve impedir acesso não autorizado :contentReference[oaicite:2]{index=2}

def test_mass_assignment_on_register(client):
    # Tenta injetar campo balance no registro
    payload = {"username": "eve", "password": "senha789", "balance": 1000000}
    resp = client.post("/register", json=payload)
    assert resp.status_code == 200
    # Eve deve começar com saldo 0, não 1M
    token = client.post("/login", json={"username": "eve", "password": "senha789"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    saldo = client.get("/balance", headers=headers).json()["balance"]
    assert saldo == 0  # previne mass assignment :contentReference[oaicite:3]{index=3}

def test_unrestricted_resource_consumption(client):
    # Envia payload de depósito gigantesco
    token = client.post("/login", json={"username": "alice", "password": "senha123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    big_amount = 10**18
    resp = client.post("/deposit", headers=headers, json={"amount": big_amount})
    # Se não houver limitação, aceitará e pode travar o sistema :contentReference[oaicite:4]{index=4}
    assert resp.status_code in (200, 400)

def test_insufficient_logging_and_monitoring(client):
    # Faz uma ação simples
    token = client.post("/login", json={"username": "alice", "password": "senha123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    client.get("/balance", headers=headers)
    # Verifica se o log foi gravado
    logs = client.get("/logs", headers=headers).json()
    assert any(l["action"] == "balance" for l in logs)  # logger mínimo :contentReference[oaicite:5]{index=5}
