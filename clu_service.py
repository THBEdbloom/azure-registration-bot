import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLU_ENDPOINT = os.getenv("CLU_ENDPOINT")
CLU_KEY = os.getenv("CLU_KEY")
CLU_PROJECT_NAME = os.getenv("CLU_PROJECT_NAME")
CLU_DEPLOYMENT_NAME = os.getenv("CLU_DEPLOYMENT_NAME")


ENTITY_MAPPING = {
    "Vorname": "first_name",
    "Nachname": "last_name",
    "Geburtsdatum": "birth_date",
    "Email": "email",
    "Telefonnummer": "phone",
    "Strasse": "street",
    "Hausnummer": "house_number",
    "PLZ": "postal_code",
    "Ort": "city",
    "Land": "country"
}


def analyze_text(text):
    if not text:
        return {}

    url = (
        f"{CLU_ENDPOINT.rstrip('/')}/"
        "language/:analyze-conversations?api-version=2023-04-01"
    )

    headers = {
        "Ocp-Apim-Subscription-Key": CLU_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "kind": "Conversation",
        "analysisInput": {
            "conversationItem": {
                "id": "1",
                "participantId": "user",
                "text": text
            }
        },
        "parameters": {
            "projectName": CLU_PROJECT_NAME,
            "deploymentName": CLU_DEPLOYMENT_NAME,
            "stringIndexType": "TextElement_V8"
        }
    }

    response = requests.post(url, headers=headers, json=body, timeout=10)
    response.raise_for_status()

    return response.json()


def extract_clu_result(text):
    result = analyze_text(text)

    prediction = result.get("result", {}).get("prediction", {})
    top_intent = prediction.get("topIntent")
    entities = prediction.get("entities", [])

    extracted_entities = {}

    for entity in entities:
        category = entity.get("category")
        text_value = entity.get("text")

        if category in ENTITY_MAPPING and text_value:
            extracted_entities[ENTITY_MAPPING[category]] = text_value

    return top_intent, extracted_entities