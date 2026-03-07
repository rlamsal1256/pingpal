import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class Settings:
    messenger_verify_token: str = field(
        default_factory=lambda: os.environ.get("MESSENGER_VERIFY_TOKEN", "dev-verify-token")
    )
    messenger_app_secret: str = field(
        default_factory=lambda: os.environ.get("MESSENGER_APP_SECRET", "dev-app-secret")
    )
    messenger_page_access_token: str = field(
        default_factory=lambda: os.environ.get("MESSENGER_PAGE_ACCESS_TOKEN", "")
    )


settings = Settings()
