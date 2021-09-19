"""
STATIC and SECRET data
"""
from pydantic import BaseSettings

from functools import lru_cache


class Settings(BaseSettings):
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_TLS: bool
    MAIL_SSL: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool
    SECRET: str
    SITE_URL: str
    SITE_NAME: str

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    '''return .env setting
    this founction just 1 time load data'''
    return Settings()
