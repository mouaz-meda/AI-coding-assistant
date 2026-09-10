from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI Coding Assistant"
    port: int = 8000
    database_url: str = "sqlite:///./data/app.db"
    secret_key: str = "dev-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
