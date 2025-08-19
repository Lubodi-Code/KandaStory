from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    # Aplicación
    APP_NAME: str = "KandaStory"
    API_PREFIX: str = "/api"
    
    # CORS - URLs permitidas para el frontend (separadas por comas)
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:3000,http://127.0.0.1:3000"

    # Base de datos MongoDB
    DB_URI: str
    DB_NAME: str = "kandastory"

    # JWT para autenticación
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Configuración de email (Gmail SMTP)
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_HOST_USER: str
    EMAIL_HOST_PASSWORD: str
    DEFAULT_FROM_EMAIL: str

    # OpenAI API
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_MAX_COMPLETION_TOKENS: int = 1024
    
    # Frontend URL used to build links in emails (include scheme, e.g. https://...)
    FRONTEND_URL: str = "http://localhost:5174"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
