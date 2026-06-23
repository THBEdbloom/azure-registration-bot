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

    APP_ID = get_secret(
        "bot-app-id"
    )

    APP_PASSWORD = get_secret(
        "bot-app-password"
    )

else:

    APP_ID = os.getenv(
        "BOT_APP_ID",
        ""
    )

    APP_PASSWORD = os.getenv(
        "BOT_APP_PASSWORD",
        ""
    )

SETTINGS = BotFrameworkAdapterSettings(
    APP_ID,
    APP_PASSWORD
)

ADAPTER = BotFrameworkAdapter(
    SETTINGS
)