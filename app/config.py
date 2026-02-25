from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REMNAWAVE_BASE_URL: str
    REMNAWAVE_API_TOKEN: str
    DEBUG: bool = False
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()