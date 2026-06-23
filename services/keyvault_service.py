import os

from dotenv import load_dotenv

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

load_dotenv()


def get_secret(name):

    key_vault_url = os.getenv(
        "KEY_VAULT_URL"
    )

    if not key_vault_url:
        raise ValueError(
            "KEY_VAULT_URL ist nicht gesetzt."
        )

    credential = DefaultAzureCredential()

    client = SecretClient(
        vault_url=key_vault_url,
        credential=credential
    )

    return client.get_secret(
        name
    ).value