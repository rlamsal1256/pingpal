from dataclasses import dataclass


@dataclass(slots=True)
class Settings:
    messenger_verify_token: str = "dev-verify-token"
    messenger_app_secret: str = "dev-app-secret"


settings = Settings()
