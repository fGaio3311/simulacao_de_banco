import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import List, Optional, Any

from fastapi import (  # type: ignore[import]
    FastAPI,
    Depends,
    HTTPException,
    status,
    BackgroundTasks
)
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import]
from fastapi.security import (  # type: ignore[import]
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)
from pydantic import BaseModel  # type: ignore[import]
from sqlalchemy import create_engine  # type: ignore[import]
from sqlalchemy.orm import sessionmaker, Session  # type: ignore[import]
from sqlalchemy.exc import SQLAlchemyError  # type: ignore[import]
import jwt  # type: ignore[import]
from jwt import JWTError  # type: ignore[import]
import paho.mqtt.client as mqtt_client  # type: ignore[import]

# Importações locais
from app.models import Base, User, Log, Transaction  # type: ignore[import]
from app.settings import Settings  # type: ignore[import]
from twin import DigitalTwin  # type: ignore[import]
from app.utils import LogsExporter  # type: ignore[import]
from app.utils import process_logs_file  # type: ignore[import]

# Carregar configurações
settings = Settings()

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
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MQTT setup ---
mqtt_client_global = mqtt_client.Client(
    client_id="api-publisher",
    protocol=mqtt_client.MQTTv311,
)
mqtt_client_global.connect(settings.mqtt_broker_host, settings.mqtt_broker_port)
mqtt_client_global.loop_start()

# --- Database setup ---
engine_kwargs: dict[str, Any] = {}

engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({
        "pool_size": int(settings.db_pool_size),
        "max_overflow": int(settings.db_max_overflow),
        "pool_timeout": int(settings.db_pool_timeout),
    })

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)
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


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
):
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
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
# ... (imports mantidos)

# ———————————————— Logger + MQTT CEP ————————————————
class DigitalTwinHandler(logging.Handler):
    def emit(self, record):
        tipo = getattr(record, "action", record.getMessage())
        user = getattr(record, "user", None)
        amount = getattr(record, "amount", None)
        to_user = getattr(record, "to_user", None)

        info = {"user": user}
        if amount is not None:
            info["amount"] = amount
        if to_user is not None:
            info["to_user"] = to_user

        descricao = f"{user} fez {tipo}"
        if tipo == "pix":
            descricao = f"{user} enviou {amount} para {to_user}"

        ev = {
            "timestamp": datetime.utcnow().isoformat(),
            "tipo": tipo,
            "info": info,
            "descricao": descricao
        }

        twin.apply_event(ev)
        mqtt_client_global.publish(f"banco/{user}/events", json.dumps(ev), qos=1)


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
    db_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    return {"message": "User created"}


@app.post("/token", response_model=Token)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(username=form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"}
        )
    token = create_access_token({"sub": user.username})
    db.add(Log(user_id=user.id, action="login", timestamp=datetime.utcnow()))
    db.commit()
    logger.info("login", extra={"user": user.username, "action": "login"})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.add(Log(
        user_id=current_user.id,
        action="balance",
        timestamp=datetime.utcnow()
    ))
    db.commit()
    logger.info(
        "balance",
        extra={"user": current_user.username, "action": "balance"}
    )
    return {"balance": current_user.balance}


@app.post("/deposit")
def deposit(
    req: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if req.amount <= 0:
        raise HTTPException(400, "Valor deve ser positivo")
    current_user.balance += req.amount
    db.add(Transaction(
        user_id=current_user.id,
        type="deposit",
        amount=req.amount
    ))
    db.add(Log(
        user_id=current_user.id,
        action="deposit",
        timestamp=datetime.utcnow()
    ))
    db.commit()
    logger.info(
        "deposit",
        extra={
            "user": current_user.username,
            "action": "deposit",
            "amount": req.amount
        }
    )
    return {"balance": current_user.balance}


@app.post("/pix")
def pix(
    req: PixRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

        db.add(Transaction(
            user_id=sender.id,
            type="pix",
            amount=req.amount
        ))
        db.add(Transaction(
            user_id=receiver.id,
            type="pix_received",
            amount=req.amount
        ))
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.error(
            "Erro ao processar pix",
            exc_info=True,
            extra={"user": current_user.username}
        )
        raise HTTPException(500, "Erro interno ao processar transferência")

    ev = {
        "timestamp": datetime.utcnow().isoformat(),
        "user": current_user.username,
        "action": "pix",
        "amount": req.amount,
        "to_user": req.to_user,
    }

    logger.info("pix", extra=ev)
    return {"balance": sender.balance}


@app.get("/logs", response_model=List[LogOut])
def get_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logs = db.query(Log).filter_by(user_id=current_user.id).all()
    return [
        LogOut(
            timestamp=log.timestamp.isoformat(),
            user=current_user.username,
            action=log.action
        )
        for log in logs
    ]


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
def load_twin(background_tasks: BackgroundTasks, path: str):
    background_tasks.add_task(lambda: process_logs_file(path, twin))
    return {"status": f"loading twin from {path}"}


@app.get("/digital-twin/stats")
def twin_stats():
    return twin.stats()


@app.get("/digital-twin/sazonalidade")
def twin_sazonalidade():
    return twin.sazonalidade()


@app.get("/digital-twin/shadow/{username}")
def twin_shadow(username: str):
    return twin.get_shadow(username)


if __name__ == "__main__":
    import uvicorn  # type: ignore[import]
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
