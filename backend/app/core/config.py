from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Elderly Health Management System MVP"
    API_V1_STR: str = "/api"
    
    SECRET_KEY: str = "supersecretkey-mvp-dev"  # Override in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./elderly_health.db"
    
    MQTT_BROKER: str = "localhost"
    MQTT_PORT: int = 1883
    MQTT_USER: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_SECRET_KEY: str = "mqtt-hmac-secret-dev"

    class Config:
        env_file = ".env"

settings = Settings()
