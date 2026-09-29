from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    database_url: str = "sqlite:///./pipeline.db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = "change-me"
    log_level: str = "INFO"
    watch_dir: str = "./inbox"
    max_file_mb: int = 25

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
