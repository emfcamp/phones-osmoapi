from pydantic_settings import BaseSettings
from os import environ


class Settings(BaseSettings):
    contact_email: str = "poc+gsmapi@emfcamp.org"
    aud2g_algo: str = "comp128v3"
    data_dir: str = environ.get("DATA_DIR", "app/data/")
    logs_dir: str = environ.get("LOGS_DIR", "logs")


settings = Settings()
