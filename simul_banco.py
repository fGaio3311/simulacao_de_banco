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

# tests/test_api.py

# ... (imports anteriores)

# --- Testes Adicionais de Validação de Entrada ---

def test_negative_or_zero_amount(client):
    # Registro e login
    client.post("/register", json={"username": "user1", "password": "pass1"})
    token = client.post("/login", json={"username": "user1", "password": "pass1"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Depósito com valor negativo
    resp = client.post("/deposit", headers=headers, json={"amount": -100})
    assert resp.status_code == 400
    assert "Valor deve ser positivo" in resp.json()["detail"]

    # Depósito com zero
    resp = client.post("/deposit", headers=headers, json={"amount": 0})
    assert resp.status_code == 400

def test_non_numeric_amount(client):
    # Login (usuário existente)
    token = client.post("/login", json={"username": "user1", "password": "pass1"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Depósito com string
    resp = client.post("/deposit", headers=headers, json={"amount": "cem"})
    assert resp.status_code == 422  # Erro de validação do Pydantic

# --- Testes de Saldo Insuficiente no PIX ---

def test_insufficient_balance_pix(client):
    # Cria usuários
    client.post("/register", json={"username": "sender", "password": "pass"})
    client.post("/register", json={"username": "receiver", "password": "pass"})

    # Login como sender
    token = client.post("/login", json={"username": "sender", "password": "pass"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Tenta transferir 100 sem saldo
    resp = client.post("/pix", headers=headers, json={"to_user": "receiver", "amount": 100})
    assert resp.status_code == 400
    assert "Saldo insuficiente" in resp.json()["detail"]

# --- Testes de Vulnerabilidades JWT ---

def test_jwt_tampering(client):
    # Gera token válido
    client.post("/register", json={"username": "victim", "password": "pass"})
    token = client.post("/login", json={"username": "victim", "password": "pass"}).json()["access_token"]

    # Modifica o token (substitui 'victim' por 'attacker' no payload)
    from jose import jwt
    payload = jwt.decode(token, options={"verify_signature": False})
    payload["sub"] = "attacker"
    fake_token = jwt.encode(payload, "secret", algorithm="HS256")  # Supondo segredo vazado

    # Tenta acessar com token modificado
    headers = {"Authorization": f"Bearer {fake_token}"}
    resp = client.get("/balance", headers=headers)
    assert resp.status_code in (401, 403)

# --- Testes de Vazamento de Informação ---

def test_login_error_leakage(client):
    # Usuário inexistente
    resp = client.post("/login", json={"username": "ghost", "password": "wrong"})
    assert resp.json()["detail"] == "Credenciais inválidas"

    # Usuário existente, senha errada
    client.post("/register", json={"username": "realuser", "password": "pass"})
    resp = client.post("/login", json={"username": "realuser", "password": "wrong"})
    assert resp.json()["detail"] == "Credenciais inválidas"  # Mesma mensagem

# --- Testes de Race Conditions ---

import threading

def test_concurrent_deposits(client):
    client.post("/register", json={"username": "raceuser", "password": "pass"})
    token = client.post("/login", json={"username": "raceuser", "password": "pass"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    def deposit():
        client.post("/deposit", headers=headers, json={"amount": 1})

    threads = [threading.Thread(target=deposit) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    resp = client.get("/balance", headers=headers)
    assert resp.json()["balance"] == 10  # Se houver race condition, pode ser <10

# --- Testes de Rate Limiting ---

def test_rate_limiting_login(client):
    for _ in range(5):
        resp = client.post("/login", json={"username": "alice", "password": "wrong"})
        assert resp.status_code == 401

    # Sexta tentativa deve ser bloqueada
    resp = client.post("/login", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 429

# --- Testes de Armazenamento de Senhas ---

def test_password_hashing(client):
    # Registra usuário
    client.post("/register", json={"username": "hashuser", "password": "pass123"})

    # Verifica no banco (usando a session)
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "hashuser").first()
    db.close()

    assert user.password != "pass123"  # Senha deve estar hasheada
    assert len(user.password) > 20  # Típico de hashes como bcrypt

# --- Testes de XSS ---

def test_xss_in_username(client):
    # Tenta registrar com username malicioso
    xss_payload = "<script>alert('xss')</script>"
    resp = client.post("/register", json={"username": xss_payload, "password": "pass"})
    assert resp.status_code == 400  # Deve bloquear input inválido

    # Se permitir, verifica se o log escapa o HTML
    token = client.post("/login", json={"username": xss_payload, "password": "pass"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    logs = client.get("/logs", headers=headers).json()
    assert "<script>" not in logs[0]["action"]
