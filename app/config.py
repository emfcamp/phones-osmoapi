from pydantic_settings import BaseSettings
from os import environ


class Settings(BaseSettings):
    contact_email: str = "poc+gsmapi@emfcamp.org"
    aud2g_algo: str = "comp128v3"
    data_dir: str = environ.get("DATA_DIR", "app/data/")
    logs_dir: str = environ.get("LOGS_DIR", "logs")

    smpp_systemid: str = environ.get("SMPP_SYSTEMID", "emfsmstooling")
    smpp_password: str = environ.get("SMPP_PASSWORD", "El3cTR1k")
    smpp_port: int = environ.get("SMPP_PORT", 2775)


settings = Settings()
