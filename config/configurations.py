from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from typing import Optional

class Configurations(BaseSettings):
    GOOGLE_API_KEY: str
    TAVILY_API_KEY: str
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def is_api_key_valid(self) -> bool:
        return bool(self.GOOGLE_API_KEY and len(self.GOOGLE_API_KEY) > 0)

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Configurations:
    settings = Configurations()
    if not settings.is_api_key_valid:
        raise ValueError("GOOGLE_API_KEY is not set or invalid. Please set a valid API key in your .env file.")
    return settings