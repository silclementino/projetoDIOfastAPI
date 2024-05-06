from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BD_URL: str = Field(default='postgresql+asyncpg://workout:workout@localhost/workout')

settings = Settings()