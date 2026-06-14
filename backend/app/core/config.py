from pydantic import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Disaster Assessment Agent"
    debug: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
