from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Coding Assistant"

    class Config:
        env_file = ".env"


settings = Settings()
