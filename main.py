import json
import requests
import logging
import hashlib
import statistics
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

import os
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from models import Base, User, Transaction, Log
import json
from paho.mqtt import client as mqtt_client

# Cria e conecta um cliente global para publicação
mqtt_client_global = mqtt_client.Client(client_id="api-publisher", protocol=mqtt_client.MQTTv311)
mqtt_client_global.connect("localhost", 1883)
mqtt_client_global.loop_start()

# --- Database Setup ---
# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")

# Se for SQLite, precisa de check_same_thread; caso contrário nenhum connect_arg
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Monta os kwargs do engine
engine_kwargs = {
    "connect_args": connect_args,
}

if not DATABASE_URL.startswith("sqlite"):
    # adiciona pool de conexões para Postgres/MySQL
    engine_kwargs.update({
        "pool_size":     int(os.getenv("DB_POOL_SIZE",     20)),
        "max_overflow":  int(os.getenv("DB_MAX_OVERFLOW",  30)),
        "pool_timeout":  int(os.getenv("DB_POOL_TIMEOUT",  30)),
    })

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
# cria tabelas se ainda não existirem
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Security & Auth ---
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# --- Pydantic Schemas ---
class UserCreate(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class DepositRequest(BaseModel):
    amount: float

class PixRequest(BaseModel):
    to_user: str
    amount: float

class LogOut(BaseModel):
    timestamp: str
    user: str
    action: str

# --- Utility Functions ---
def get_password_hash(password: str) -> str:
    # SHA256 hex length 64 (>20 chars)
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

# --- JWT Token Management ---
from datetime import timedelta

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# --- Digital Twin ---
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

    def apply_event(self, event: dict):
        ts = event.get("timestamp")
        try:
            timestamp = datetime.fromisoformat(ts)
        except Exception:
            timestamp = None
        user = event.get("user")
        action = event.get("action")
        if not user or not action:
            return
        estado = self.users[user]
        if action == "login":
            estado["ultimo_login"] = timestamp
            estado["n_logins"] += 1
            if timestamp:
                estado["login_timestamps"].append(timestamp)
        elif action == "balance":
            estado["n_consultas_saldo"] += 1
        elif action == "deposit":
            amt = event.get("amount", 0)
            try:
                amt = float(amt)
            except:
                amt = 0
            estado["saldo"] += amt
            estado["total_depositado"] += amt
            estado["n_depositos"] += 1
            estado["deposit_amounts"].append(amt)
        elif action == "pix":
            amt = event.get("amount", 0)
            try:
                amt = float(amt)
            except:
                amt = 0
            to_user = event.get("to_user")
            estado["saldo"] -= amt
            estado["total_pix_enviado"] += amt
            estado["n_pix"] += 1
            estado["pix_amounts_enviados"].append(amt)
            if to_user:
                recv = self.users[to_user]
                recv["saldo"] += amt
                recv["total_pix_recebido"] += amt
                recv["pix_amounts_recebidos"].append(amt)

    def summary(self):
        report = {}
        for user, estado in self.users.items():
            report[user] = {
                "saldo": estado["saldo"],
                "ultimo_login": estado["ultimo_login"].isoformat() if estado["ultimo_login"] else None,
                "n_logins": estado["n_logins"],
                "n_consultas_saldo": estado["n_consultas_saldo"],
                "total_depositado": estado["total_depositado"],
                "n_depositos": estado["n_depositos"],
                "total_pix_enviado": estado["total_pix_enviado"],
                "total_pix_recebido": estado["total_pix_recebido"],
                "n_pix": estado["n_pix"]
            }
        return report

class LogsExporter:
    def __init__(self, api_base_url: str, token: str, output_path: str):
        self.api_base_url = api_base_url.rstrip("/")
        self.token = token
        self.output_path = output_path

    def fetch_all_logs(self):
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(f"{self.api_base_url}/logs", headers=headers)
        resp.raise_for_status()
        return resp.json()

    def write_to_file(self):
        events = self.fetch_all_logs()
        with open(self.output_path, "w", encoding="utf-8") as f:
            for ev in events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")


def process_logs_file(file_path: str, twin: DigitalTwin):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except:
                continue
            twin.apply_event(ev)

# --- Logger & Handler ---
twin = DigitalTwin()
logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)

class DigitalTwinHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        from datetime import datetime
        ev = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "user": getattr(record, "user", None),
            "action": getattr(record, "action", record.getMessage()),
        }
        # inclui amount e to_user, se existirem no record
        if hasattr(record, "amount"):
            ev["amount"] = getattr(record, "amount")
        if hasattr(record, "to_user"):
            ev["to_user"] = getattr(record, "to_user")

        twin.apply_event(ev)
        result = mqtt_client_global.publish(f"banco/{ev['user']}/events",
                                            json.dumps(ev), qos=1)
        print(f"[MQTT PUBLISH] tópico=banco/{ev['user']}/events  mid={result.mid}")



handler = DigitalTwinHandler()
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger.addHandler(handler)

# --- FastAPI Application ---
app = FastAPI(title="Bank Simulator with Digital Twin", version="0.1.0")

@app.get("/ping")
def ping():
    return {"pong": True}

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = get_password_hash(user.password)
    db_user = User(username=user.username, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    return {"message": "User created"}

@app.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}
    )
    # log event
    db.add(Log(user_id=user.id, action="login", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("login", extra={"user": user.username, "action": "login"})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/balance")
def get_balance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(Log(user_id=current_user.id, action="balance", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("balance", extra={"user": current_user.username, "action": "balance"})
    return {"balance": current_user.balance}

@app.post("/deposit")
def deposit(
    req: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.amount <= 0:
        raise HTTPException(status_code=400, detail="Valor deve ser positivo")
    current_user.balance += req.amount
    db.add(Transaction(user_id=current_user.id, type="deposit", amount=req.amount))
    db.add(Log(user_id=current_user.id, action="deposit", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("deposit", extra={"user": current_user.username, "action": "deposit", "amount": req.amount})
    return {"balance": current_user.balance}

@app.post("/pix")
def pix(
    req: PixRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")

    # tudo dentro de um único transaction block
    try:
        with db.begin():
            # bloqueia as linhas para evitar condições de corrida
            sender = (
                db.query(User)
                  .filter(User.id == current_user.id)
                  .with_for_update()
                  .one()
            )
            recipient = (
                db.query(User)
                  .filter(User.username == req.to_user)
                  .with_for_update()
                  .first()
            )
            if not recipient:
                raise HTTPException(404, "Usuário destinatário não encontrado")
            if sender.balance < req.amount:
                raise HTTPException(400, "Saldo insuficiente")

            sender.balance -= req.amount
            recipient.balance += req.amount

            tx = Transaction(
                user_id=sender.id, type="pix", amount=req.amount,
                to_user=req.to_user  # ajuste no seu modelo se precisar
            )
            db.add(tx)
    except HTTPException:
        # já convertido em resposta apropriada
        raise
    except Exception:
        # log geral, mas não vaza detalhes pro cliente
        logger.error("erro ao processar pix", exc_info=True, extra={"user": current_user.username})
        raise HTTPException(500, "Erro interno ao processar transferência")

    # após commit, posso publicar com segurança
    ev = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": current_user.username,
        "action": "pix",
        "amount": req.amount,
        "to_user": req.to_user
    }
    mqtt_client_global.publish(f"banco/{current_user.username}/events", json.dumps(ev), qos=1)
    logger.info("pix", extra=ev)

    return {"balance": sender.balance}


@app.get("/logs", response_model=List[LogOut])
def get_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db_logs = db.query(Log).filter(Log.user_id == current_user.id).all()
    out = [LogOut(
        timestamp=log.timestamp.isoformat(),
        user=current_user.username,
        action=log.action
    ) for log in db_logs]
    return out

@app.get("/digital-twin/summary")
def twin_summary():
    return twin.summary()

@app.post("/digital-twin/export")
def export_logs(
    background_tasks: BackgroundTasks,
    api_base_url: str,
    token: str,
    path: str
):
    exporter = LogsExporter(api_base_url, token, path)
    background_tasks.add_task(exporter.write_to_file)
    return {"status": f"exporting to {path}"}

@app.post("/digital-twin/load")
def load_twin(
    background_tasks: BackgroundTasks,
    path: str
):
    background_tasks.add_task(process_logs_file, path, twin)
    return {"status": f"loading twin from {path}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)