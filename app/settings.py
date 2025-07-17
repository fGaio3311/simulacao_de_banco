# app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # configurações do próprio FastAPI
    title: str = "Bank Simulator with Digital Twin"
    version: str = "0.1.0"
        # variáveis extras do frontend


    # banco de dados
    database_url: str = "sqlite:///./test.db"
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30

    # autenticação / JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # MQTT
# settings.py define em snake_case:
    mqtt_broker_host: str = "mqtt-broker"
    mqtt_broker_port: int = 1883


    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    react_app_api_url: str = "http://localhost:8000"

    # diz onde fica seu .env
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    # Corrigir indentação e quebras de linha
    DATABASE_CONFIG = {
        "host": "localhost",
        "user": "root",
        "password": "password",
        "database": "digital_twin_db"
    }
