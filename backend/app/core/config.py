from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "LLM Agents"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ELEVENLABS_API_KEY: str
    OPENROUTER_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()