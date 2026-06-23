import os
import requests
import azure.cognitiveservices.speech as speechsdk

from dotenv import load_dotenv

from services.keyvault_service import get_secret

load_dotenv()

USE_KEY_VAULT = os.getenv("USE_KEY_VAULT", "false").lower() == "true"

if USE_KEY_VAULT:
    SPEECH_KEY = get_secret("speech-key")
    SPEECH_REGION = get_secret("speech-region")
else:
    SPEECH_KEY = os.getenv("SPEECH_KEY")
    SPEECH_REGION = os.getenv("SPEECH_REGION")


def get_speech_token():

    url = (
        f"https://{SPEECH_REGION}.api.cognitive.microsoft.com/"
        "sts/v1.0/issueToken"
    )

    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY
    }

    response = requests.post(
        url,
        headers=headers,
        timeout=10
    )

    response.raise_for_status()

    return response.text, SPEECH_REGION


def synthesize_speech_to_file(
    text,
    output_file="static/bot_response.wav"
):

    speech_config = speechsdk.SpeechConfig(
        subscription=SPEECH_KEY,
        region=SPEECH_REGION
    )

    speech_config.speech_synthesis_language = "de-DE"

    speech_config.speech_synthesis_voice_name = (
        "de-DE-KatjaNeural"
    )

    audio_config = speechsdk.audio.AudioOutputConfig(
        filename=output_file
    )

    synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config,
        audio_config=audio_config
    )

    result = synthesizer.speak_text_async(
        text
    ).get()

    return (
        result.reason
        == speechsdk.ResultReason.SynthesizingAudioCompleted
    )