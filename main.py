import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session
from paho.mqtt import client as mqtt_client

from models import Base, User, Transaction, Log
from app.settings import Settings

# load all your env-backed settings
settings = Settings()
from twin import twin

import os, json, logging, hashlib
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
# … seus outros imports …

# ————————————————————————————————————————
# 1) CRIE só uma vez o app e monte o CORS
# ————————————————————————————————————————
app = FastAPI(title="Bank Simulator with Digital Twin", version="0.1.0")

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,    # ou ["*"] só em dev
    allow_credentials=True,
    allow_methods=["*"],      # GET, POST, OPTIONS, PUT…
    allow_headers=["*"],      # Authorization, Content-Type…
)

# --- MQTT setup ---
mqtt_client_global = mqtt_client.Client(
    client_id="api-publisher",
    protocol=mqtt_client.MQTTv311,
)
# main.py (linha 58)
mqtt_client_global.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
mqtt_client_global.loop_start()

# --- Database setup ---
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size":    settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout,
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Auth setup ---
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

def get_password_hash(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def verify_password(plain: str, hashed: str) -> bool:
    return get_password_hash(plain) == hashed

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    creds_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise creds_exc
    except JWTError:
        raise creds_exc

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise creds_exc
    return user

# --- Pydantic schemas ---
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

twin = DigitalTwin()

# Logging handler that feeds the digital twin and MQTT
class DigitalTwinHandler(logging.Handler):
    def emit(self, record):
        ev = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "user": getattr(record, "user", None),
            "action": getattr(record, "action", record.getMessage()),
        }
        if hasattr(record, "amount"):
            ev["amount"] = record.amount
        if hasattr(record, "to_user"):
            ev["to_user"] = record.to_user

        twin.apply_event(ev)
        mqtt_client_global.publish(f"banco/{ev['user']}/events", json.dumps(ev), qos=1)

logger = logging.getLogger("myapp")
logger.setLevel(logging.INFO)
logger.addHandler(DigitalTwinHandler())

# --- Endpoints ---
@app.get("/ping")
def ping():
    return {"pong": True}

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter_by(username=user.username).first():
        raise HTTPException(400, "Username already registered")
    db_user = User(username=user.username, hashed_password=get_password_hash(user.password))
    db.add(db_user)
    db.commit()
    return {"message": "User created"}

@app.post("/token", response_model=Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(username=form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciais inválidas", headers={"WWW-Authenticate":"Bearer"})
    token = create_access_token({"sub": user.username})
    db.add(Log(user_id=user.id, action="login", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("login", extra={"user":user.username, "action":"login"})
    return {"access_token": token, "token_type":"bearer"}

@app.get("/balance")
def get_balance(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.add(Log(user_id=current_user.id, action="balance", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("balance", extra={"user":current_user.username, "action":"balance"})
    return {"balance": current_user.balance}

@app.post("/deposit")
def deposit(req: DepositRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")
    current_user.balance += req.amount
    db.add(Transaction(user_id=current_user.id, type="deposit", amount=req.amount))
    db.add(Log(user_id=current_user.id, action="deposit", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("deposit", extra={"user":current_user.username, "action":"deposit", "amount":req.amount})
    return {"balance": current_user.balance}

@app.post("/pix")
def pix(req: PixRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")
    recipient = db.query(User).filter_by(username=req.to_user).first()
    if not recipient:
        raise HTTPException(404, "Usuário destinatário não encontrado")
    if current_user.balance < req.amount:
        raise HTTPException(400, "Saldo insuficiente")

    try:
        sender = db.query(User).filter_by(id=current_user.id).with_for_update().one()
        receiver = db.query(User).filter_by(id=recipient.id).with_for_update().one()

        sender.balance -= req.amount
        receiver.balance += req.amount

        db.add(Transaction(user_id=sender.id,   type="pix",          amount=req.amount))
        db.add(Transaction(user_id=receiver.id, type="pix_received", amount=req.amount))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.error("Erro ao processar pix", exc_info=True, extra={"user":current_user.username})
        raise HTTPException(500, "Erro interno ao processar transferência")

    ev = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": current_user.username,
        "action": "pix",
        "amount": req.amount,
        "to_user": req.to_user,
    }
    mqtt_client_global.publish(f"banco/{current_user.username}/events", json.dumps(ev), qos=1)
    logger.info("pix", extra=ev)
    return {"balance": sender.balance}

@app.get("/logs", response_model=List[LogOut])
def get_logs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logs = db.query(Log).filter_by(user_id=current_user.id).all()
    return [
        LogOut(timestamp=l.timestamp.isoformat(), user=current_user.username, action=l.action)
        for l in logs
    ]

@app.get("/digital-twin/summary")
def twin_summary():
    return twin.summary()

@app.post("/digital-twin/export")
def export_logs(background_tasks: BackgroundTasks, api_base_url: str, token: str, path: str):
    from app.utils import LogsExporter
    exporter = LogsExporter(api_base_url, token, path)
    background_tasks.add_task(exporter.write_to_file)
    return {"status": f"exporting to {path}"}

@app.post("/digital-twin/load")
def load_twin(background_tasks: BackgroundTasks, path: str):
    background_tasks.add_task(lambda: process_logs_file(path, twin))
    return {"status": f"loading twin from {path}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
