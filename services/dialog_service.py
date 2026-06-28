from dataclasses import dataclass, field

from repositories.user_repository import save_user
from services.clu_service import extract_clu_result
from utils.validators import (
    validate_field,
    normalize_field
)


REQUIRED_FIELDS = [
    "first_name",
    "last_name",
    "birth_date",
    "email",
    "phone",
    "street",
    "house_number",
    "postal_code",
    "city",
    "country"
]


FIELD_QUESTIONS = {
    "first_name": "Wie lautet dein Vorname?",
    "last_name": "Wie lautet dein Nachname?",
    "birth_date": "Wann wurdest du geboren?",
    "email": "Wie lautet deine E-Mail-Adresse?",
    "phone": "Wie lautet deine Telefonnummer?",
    "street": "Wie lautet deine Straße?",
    "house_number": "Wie lautet deine Hausnummer?",
    "postal_code": "Wie lautet deine Postleitzahl?",
    "city": "In welchem Ort wohnst du?",
    "country": "In welchem Land wohnst du?"
}


FIELD_LABELS = {
    "first_name": "Vorname",
    "last_name": "Nachname",
    "birth_date": "Geburtsdatum",
    "email": "E-Mail",
    "phone": "Telefonnummer",
    "street": "Straße",
    "house_number": "Hausnummer",
    "postal_code": "Postleitzahl",
    "city": "Ort",
    "country": "Land"
}


CONFIRM_WORDS = {
    "ja",
    "yes",
    "korrekt",
    "passt",
    "stimmt",
    "richtig"
}


REJECT_WORDS = {
    "nein",
    "falsch",
    "nicht korrekt",
    "passt nicht",
    "stimmt nicht"
}


@dataclass
class ChatSession:
    started: bool = False
    awaiting_confirmation: bool = False
    awaiting_correction: bool = False
    user_data: dict = field(default_factory=dict)
    failed_attempts: int = 0


class DialogManager:

    def __init__(self):
        self.sessions = {}

    def get_session(self, session_id):

        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession()

        return self.sessions[session_id]

    def reset_session(self, session_id):

        if session_id in self.sessions:
            del self.sessions[session_id]

    def handle_message(self, session_id, message):

        message = self.clean_user_input(message)

        session = self.get_session(session_id)

        intent = None
        entities = {}

        try:
            intent, entities = extract_clu_result(message)

            entities = self.fix_name_entities(
                message,
                entities
            )

        except Exception as e:
            print("CLU ERROR:", e)

        print("MESSAGE:", message)
        print("INTENT:", intent)
        print("ENTITIES:", entities)

        if self.is_help(intent, message):
            return {
                "reply": self.create_help_message(session)
            }

        if self.is_cancel(intent, message):

            self.reset_session(session_id)

            return {
                "reply": (
                    "Die Registrierung wurde abgebrochen. "
                    "Du kannst jederzeit neu beginnen."
                )
            }

        if self.is_restart(intent, message):

            self.reset_session(session_id)

            session = self.get_session(session_id)
            session.started = True

            return {
                "reply": (
                    "Die Registrierung wurde neu gestartet.\n\n"
                    "Wir beginnen wieder von vorne.\n\n"
                    + FIELD_QUESTIONS["first_name"]
                )
            }

        if not session.started:

            if self.is_start(intent, message):
                session.started = True

                return {
                    "reply": (
                        "Super. Lass uns beginnen.\n\n"
                        + FIELD_QUESTIONS["first_name"]
                    )
                }

            if entities:
                session.started = True

            else:
                return {
                    "reply": (
                        "Hallo! Ich bin dein Registrierungsassistent.\n\n"
                        "Du kannst 'Registrierung starten' sagen "
                        "oder direkt deine Daten nennen."
                    )
                }

        if session.awaiting_confirmation:

            return self.handle_confirmation(
                session_id,
                session,
                message,
                intent,
                entities
            )

        return self.handle_registration(
            session,
            message,
            intent,
            entities
        )

    def handle_confirmation(
        self,
        session_id,
        session,
        message,
        intent,
        entities
    ):

        lowered = message.lower().strip()

        if session.awaiting_correction:

            if (
                lowered in CONFIRM_WORDS
                or self.is_confirm(intent)
                or "alles korrekt" in lowered
                or "angaben sind korrekt" in lowered
                or "doch" == lowered
            ):

                save_user(session.user_data)

                self.reset_session(session_id)

                return {
                    "reply": (
                        "Vielen Dank.\n\n"
                        "Der Benutzeraccount wurde erfolgreich gespeichert."
                    )
                }

        if (
            lowered in CONFIRM_WORDS
            or self.is_confirm(intent)
        ):

            save_user(session.user_data)

            self.reset_session(session_id)

            return {
                "reply": (
                    "Vielen Dank.\n\n"
                    "Der Benutzeraccount wurde erfolgreich gespeichert."
                )
            }

        if (
            lowered in REJECT_WORDS
            or self.is_reject(intent)
        ):
            
            session.awaiting_correction = True

            return {
                "reply": (
                    "Kein Problem.\n\n"
                    "Nenne mir einfach die Angabe, "
                    "die korrigiert werden soll."
                )
            }

        if entities:

            session.awaiting_correction = False

            result = self.apply_entities(
                session,
                entities
            )

            return {
                "reply": (
                    result
                    + "\n\n"
                    + self.create_summary(session.user_data)
                    + "\n\nSind diese Angaben jetzt korrekt?"
                )
            }

        return {
            "reply": (
                "Bitte bestätige mit Ja "
                "oder nenne mir die korrigierte Angabe."
            )
        } 

    def try_extract_email_from_speech(self, message):

        words = message.lower().split()

        start_index = 0

        for i, word in enumerate(words):

            if (
                word in ["at", "ät", "@"]
                or "@" in word
            ):
                start_index = max(0, i - 1)
                break

        candidate = " ".join(
            words[start_index:]
        )

        email = normalize_field(
            "email",
            candidate
        )

        is_valid, _ = validate_field(
            "email",
            email
        )

        if is_valid:
            return email

        return None

    def try_extract_phone_from_speech(self, message):

        replacements = {
            "plus": "+",
            "null": "0",
            "eins": "1",
            "zwei": "2",
            "drei": "3",
            "vier": "4",
            "fünf": "5",
            "fuenf": "5",
            "sechs": "6",
            "sieben": "7",
            "acht": "8",
            "neun": "9"
        }

        value = message.lower()

        for old, new in replacements.items():

            value = value.replace(
                old,
                new
            )

        phone = normalize_field(
            "phone",
            value
        )

        is_valid, _ = validate_field(
            "phone",
            phone
        )

        if is_valid:
            return phone

        return None

    def handle_registration(
        self,
        session,
        message,
        intent,
        entities
    ):

        applied_message = ""

        if entities:

            applied_message = self.apply_entities(
                session,
                entities
            )

            missing_field = self.get_next_missing_field(
                session.user_data
            )

            if missing_field == "email":

                speech_email = self.try_extract_email_from_speech(
                    message
                )

                if speech_email:

                    session.user_data["email"] = speech_email

                    next_field = self.get_next_missing_field(
                        session.user_data
                    )

                    return {
                        "reply": (
                            f"✓ E-Mail gespeichert: {speech_email}"
                            + "\n\n"
                            + FIELD_QUESTIONS[next_field]
                        )
                    }


            if missing_field == "phone":

                speech_phone = self.try_extract_phone_from_speech(
                    message
                )

                if speech_phone:

                    session.user_data["phone"] = speech_phone

                    next_field = self.get_next_missing_field(
                        session.user_data
                    )

                    return {
                        "reply": (
                            f"✓ Telefonnummer gespeichert: {speech_phone}"
                            + "\n\n"
                            + FIELD_QUESTIONS[next_field]
                        )
                    }

            if not missing_field:

                session.awaiting_confirmation = True

                return {
                    "reply": (
                        applied_message
                        + "\n\n"
                        + self.create_summary(
                            session.user_data
                        )
                        + "\n\nSind diese Angaben korrekt?"
                    )
                }

            return {
                "reply": (
                    applied_message
                    + "\n\n"
                    + "Als Nächstes benötige ich:\n"
                    + FIELD_QUESTIONS[missing_field]
                )
            }

        missing_field = self.get_next_missing_field(
            session.user_data
        )

        if not missing_field:

            session.awaiting_confirmation = True

            return {
                "reply": (
                    self.create_summary(
                        session.user_data
                    )
                    + "\n\nSind diese Angaben korrekt?"
                )
            }

        normalized_value = normalize_field(
            missing_field,
            self.normalize_value(
                missing_field,
                message
            )
        )

        is_valid, error_message = validate_field(
            missing_field,
            normalized_value
        )

        if not is_valid:

            session.failed_attempts += 1

            reply = (
                error_message
                + "\n\n"
                + FIELD_QUESTIONS[missing_field]
            )

            if session.failed_attempts >= 3:

                reply += (
                    "\n\nBeispiel:\n"
                    + self.get_example_for_field(
                        missing_field
                    )
                )

            return {
                "reply": reply
            }

        session.failed_attempts = 0

        session.user_data[
            missing_field
        ] = normalized_value

        saved_text = (
            f"✓ {FIELD_LABELS[missing_field]}: "
            f"{normalized_value}"
        )

        next_field = self.get_next_missing_field(
            session.user_data
        )

        if not next_field:

            session.awaiting_confirmation = True

            return {
                "reply": (
                    saved_text
                    + "\n\n"
                    + self.create_summary(
                        session.user_data
                    )
                    + "\n\nSind diese Angaben korrekt?"
                )
            }

        return {
            "reply": (
                saved_text
                + "\n\n"
                + FIELD_QUESTIONS[next_field]
            )
        }

    def apply_entities(
        self,
        session,
        entities
    ):

        messages = []

        for field_name, value in entities.items():

            if field_name not in REQUIRED_FIELDS:
                continue

            normalized_value = normalize_field(
                field_name,
                self.normalize_value(
                    field_name,
                    value
                )
            )

            is_valid, _ = validate_field(
                field_name,
                normalized_value
            )

            if not is_valid:
                continue

            existing_value = session.user_data.get(
                field_name
            )

            session.user_data[
                field_name
            ] = normalized_value

            if existing_value:

                messages.append(
                    f"✓ {FIELD_LABELS[field_name]} aktualisiert: "
                    f"{normalized_value}"
                )

            else:

                messages.append(
                    f"✓ {FIELD_LABELS[field_name]} gespeichert: "
                    f"{normalized_value}"
                )

        if not messages:

            return (
                "Ich konnte daraus leider keine "
                "gültigen Angaben übernehmen."
            )

        return "\n".join(messages)

    def get_next_missing_field(
        self,
        user_data
    ):

        for field in REQUIRED_FIELDS:

            if not user_data.get(field):
                return field

        return None

    def create_summary(
        self,
        user_data
    ):

        return f"""
Bitte prüfe deine Angaben:

Vorname: {user_data.get("first_name")}
Nachname: {user_data.get("last_name")}
Geburtsdatum: {user_data.get("birth_date")}
E-Mail: {user_data.get("email")}
Telefonnummer: {user_data.get("phone")}
Straße: {user_data.get("street")}
Hausnummer: {user_data.get("house_number")}
Postleitzahl: {user_data.get("postal_code")}
Ort: {user_data.get("city")}
Land: {user_data.get("country")}
""".strip()

    def create_help_message(self, session):

        text = (
            "Ich unterstütze dich bei der Registrierung.\n\n"
        )

        if not session.started:
            return (
                text
                + "Schreibe einfach 'Start', um die Registrierung zu beginnen."
            )
        
        if session.awaiting_correction:
            return (
                text
                + "Nenne einfach die Angabe, die geändert werden soll.\n\n"
                + "Beispiele:\n"
                + "• Meine E-Mail ist max@example.de\n"
                + "• Meine Telefonnummer ist +4915112345678\n"
                + "• Mein Nachname ist Mustermann"
            )

        if session.awaiting_confirmation:
            return (
                text
                + "Bitte bestätige deine Angaben mit 'Ja' oder antworte mit 'Nein', wenn etwas geändert werden soll."
            )

        missing = self.get_next_missing_field(session.user_data)

        if missing:
            return (
                text
                + "Aktuell benötige ich folgende Angabe:\n\n"
                + FIELD_QUESTIONS[missing]
            )

        return text

    def get_example_for_field(
        self,
        field_name
    ):

        examples = {
            "first_name":
                "Mein Vorname ist Max",

            "last_name":
                "Mein Nachname ist Mustermann",

            "birth_date":
                "20.01.2000",

            "email":
                "max.mustermann@example.de",

            "phone":
                "+49 151 12345678",

            "street":
                "Musterstraße",

            "house_number":
                "12a",

            "postal_code":
                "12345",

            "city":
                "Berlin",

            "country":
                "Deutschland"
        }

        return examples.get(
            field_name,
            "Bitte gib die Angabe erneut ein."
        )
    
    def clean_user_input(
        self,
        value
    ):

        if not value:
            return ""

        return value.strip().rstrip(
            ".!?;,"
        )

    def normalize_value(
        self,
        field_name,
        value
    ):

        value = self.clean_user_input(
            value
        )

        replacements = [
            "mein vorname ist ",
            "mein nachname ist ",
            "mein name ist ",
            "ich heiße ",
            "ich heisse ",
            "meine e-mail ist ",
            "meine email ist ",
            "meine mail ist ",
            "email ist ",
            "e-mail ist ",
            "mail ist ",
            "meine telefonnummer ist ",
            "telefonnummer ist ",
            "telefon ist ",
            "meine nummer ist ",
            "meine adresse ist ",
            "adresse ist ",
            "ich wohne in ",
            "ich wohne "
        ]

        lowered = value.lower()

        for prefix in replacements:

            if lowered.startswith(prefix):

                value = value[
                    len(prefix):
                ].strip()

                break

        if field_name == "country":

            value = (
                value
                .replace("In ", "")
                .replace("in ", "")
                .strip()
            )

        return self.clean_user_input(
            value
        )
    
    def fix_name_entities(
        self,
        message,
        entities
    ):

        if not entities:
            return entities

        message_lower = message.lower()

        if "vorname" in message_lower:
            entities.pop(
                "last_name",
                None
            )

        if "nachname" in message_lower:
            entities.pop(
                "first_name",
                None
            )

        if (
            "first_name" in entities
            and "last_name" in entities
            and entities["first_name"].lower()
            == entities["last_name"].lower()
        ):
            entities.pop(
                "last_name",
                None
            )

        return entities

    def is_start(
        self,
        intent,
        message
    ):

        if intent:
            return (
                intent.lower()
                == "startregistration"
            )

        lowered = message.lower()

        return any(
            word in lowered
            for word in [
                "start",
                "registrierung",
                "beginnen"
            ]
        )

    def is_help(
        self,
        intent,
        message
    ):

        if intent:
            return (
                intent.lower()
                == "help"
            )

        return (
            "hilfe"
            in message.lower()
        )

    def is_cancel(
        self,
        intent,
        message
    ):

        if intent:
            return (
                intent.lower()
                == "cancelregistration"
            )

        return any(
            word in message.lower()
            for word in [
                "abbrechen",
                "abbruch",
                "cancel"
            ]
        )

    def is_restart(
        self,
        intent,
        message
    ):

        if intent:
            return (
                intent.lower()
                == "restartregistration"
            )

        return any(
            word in message.lower()
            for word in [
                "neu starten",
                "neustart",
                "restart"
            ]
        )

    def is_confirm(
        self,
        intent
    ):

        if not intent:
            return False

        return (
            intent.lower()
            == "confirmdata"
        )

    def is_reject(
        self,
        intent
    ):

        if not intent:
            return False

        return (
            intent.lower()
            == "correctdata"
        )


dialog_manager = DialogManager()


def handle_chat_message(
    session_id,
    message
):

    return dialog_manager.handle_message(
        session_id,
        message
    )