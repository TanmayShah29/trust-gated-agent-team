from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "TrustChain"
    database_url: str = "postgresql+asyncpg://trustchain:trustchain@localhost:5432/trustchain"
    database_url_sync: str = "postgresql+psycopg2://trustchain:trustchain@localhost:5432/trustchain"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    max_retries: int = 2
    chain_verify_batch_size: int = 100

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
