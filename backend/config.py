from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    gemini_api_key: str = ""
    elevenlabs_api_key: str = ""
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    simulation_speed: float = 1.0

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()
