from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "API Gestion de Revendedores"
    app_env: str = "development"
    api_prefix: str = "/api"
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500"
    oracle_user: str = ""
    oracle_password: str = ""
    oracle_dsn: str = ""
    tns_admin: str = ""
    wallet_password: str = ""
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 60

    model_config = SettingsConfigDict(env_file="backend/.env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
