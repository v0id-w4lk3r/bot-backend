from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ENVIRONMENT
    ENV: str = "production"

    # DATABASE
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "my_bot_db"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""

    DB_ECHO: bool = False
    DB_CREATE_TABLES: bool = False
    DB_CONNECT_TIMEOUT: float = 5.0

    # DISCORD OAUTH2
    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_REDIRECT_URI: str = ""
    DISCORD_OAUTH_SCOPES: str = "identify guilds"

    # SECURITY
    SECRET_KEY: str = "change-me"
    ALLOWED_ORIGINS: str = "http://localhost:3000"
    SESSION_COOKIE_NAME: str = "bot_panel_session"
    OAUTH_STATE_COOKIE_NAME: str = "discord_oauth_state"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 7
    AUTH_SUCCESS_REDIRECT_URL: str = ""
    AUTH_FAILURE_REDIRECT_URL: str = ""

    # ASSETS
    AFK_IMAGE_URL: str = ""
    MENTION_GIF_URL: str = ""
    HELP_BANNER_GIF: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins_list(self) -> list[str]:
        return [
            origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}"
            f"/{self.DB_NAME}"
        )

    @property
    def auth_success_redirect_url(self) -> str:
        return self.AUTH_SUCCESS_REDIRECT_URL or self.allowed_origins_list[0]

    @property
    def auth_failure_redirect_url(self) -> str:
        return self.AUTH_FAILURE_REDIRECT_URL or self.auth_success_redirect_url

    @property
    def secure_cookies(self) -> bool:
        return self.ENV.lower() == "production"


settings = Settings()
