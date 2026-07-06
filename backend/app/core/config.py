from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://mailpilot:mailpilot@localhost:5432/mailpilot"
    ai_provider: str = "mock"
    cors_origins: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}


settings = Settings()
