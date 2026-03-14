from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    database_url: str = "sqlite+aiosqlite:///./data/redpill_radar.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
