from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://mailpilot:mailpilot@localhost:5432/mailpilot"
    ai_provider: str = "mock"
    cors_origins: str = "http://localhost:5173"

    # OpenAI-compatible (OpenAI, DeepSeek, Ollama, vLLM, etc.)
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_base_url: str = "https://api.anthropic.com"
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Auth
    jwt_secret_key: str = "change-me-in-production"

    # Encryption key for sensitive stored data (Fernet key, auto-generated if unset)
    encryption_key: str = ""

    # Gmail OAuth
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_redirect_uri: str = ""
    gmail_scopes: str = "openid email https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send"
    gmail_oauth_success_url: str = "http://localhost:5173/settings?gmail=connected"
    gmail_oauth_failure_url: str = "http://localhost:5173/settings?gmail=error"

    # Outlook / Microsoft Graph OAuth
    outlook_client_id: str = ""
    outlook_client_secret: str = ""
    outlook_redirect_uri: str = ""
    outlook_scopes: str = "offline_access User.Read Mail.Read Mail.Send"
    outlook_oauth_success_url: str = "http://localhost:5173/settings?outlook=connected"
    outlook_oauth_failure_url: str = "http://localhost:5173/settings?outlook=error"

    # AI call reliability
    ai_request_timeout: float = 30.0
    ai_max_retries: int = 1
    ai_rate_limit_per_minute: int = 30

    model_config = {"env_file": ".env"}


settings = Settings()
