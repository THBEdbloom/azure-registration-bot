import os

from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings
)

from services.keyvault_service import get_secret


USE_KEY_VAULT = (
    os.getenv("USE_KEY_VAULT", "false").lower()
    == "true"
)

if USE_KEY_VAULT:
    APP_ID = get_secret("bot-app-id")
    APP_PASSWORD = get_secret("bot-app-password")
    APP_TENANT_ID = get_secret("bot-tenant-id")
else:
    APP_ID = os.getenv("BOT_APP_ID", "")
    APP_PASSWORD = os.getenv("BOT_APP_PASSWORD", "")
    APP_TENANT_ID = os.getenv("BOT_TENANT_ID", "")


SETTINGS = BotFrameworkAdapterSettings(
    APP_ID,
    APP_PASSWORD,
    channel_auth_tenant=APP_TENANT_ID
)

ADAPTER = BotFrameworkAdapter(
    SETTINGS
)