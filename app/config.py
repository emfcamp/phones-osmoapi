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

    gsm_system_number: int = 476
    gsm_system_imsi: int = 999001234599999

    pyhss_base_url: str = "http://vm-phones07.emf.camp:8080/"
    # only needed if lock_provisioning: true in pyHSS's config.yaml
    pyhss_provisioning_key: str | None = None
    pyhss_default_amf: str = "8000"
    # "3" = 3G Milenage w/ 2G keys, per pyHSS's algo field docs
    pyhss_2g_algo: str = "3"
    pyhss_default_apn_id: int = 1


settings = Settings()
