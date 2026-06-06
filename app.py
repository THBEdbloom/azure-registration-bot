import csv
import io
import json
from datetime import datetime

from flask import Flask, render_template, request, jsonify, Response
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from database import init_db, save_user, get_all_users, search_users, get_statistics
from validators import validate_field, normalize_field
from clu_service import extract_clu_result
from speech_service import synthesize_speech_to_file, get_speech_token


app = Flask(__name__)
app.secret_key = "dev-secret-key"


FIELDS = [
    ("first_name", "Wie heißt du?"),
    ("last_name", "Wie heißt du?"),
    ("birth_date", "Wann wurdest du geboren?"),
    ("email", "Wie lautet deine E-Mail-Adresse?"),
    ("phone", "Wie lautet deine Telefonnummer?"),
    ("street", "Wie lautet deine vollständige Adresse?"),
    ("house_number", "Wie lautet deine vollständige Adresse?"),
    ("postal_code", "Wie lautet deine vollständige Adresse?"),
    ("city", "Wie lautet deine vollständige Adresse?"),
    ("country", "Wie lautet deine vollständige Adresse?")
]

CLU_ENTITY_MAPPING = {
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

CONFIRM_WORDS = ["ja", "jap", "yes", "korrekt", "passt", "stimmt", "richtig"]
CORRECT_WORDS = ["nein", "ne", "no", "falsch", "nicht korrekt", "passt nicht", "stimmt nicht"]

sessions = {}


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    session_id = data.get("session_id", "default")
    message = clean_user_input(data.get("message", ""))
    display_message = message

    if session_id not in sessions:
        sessions[session_id] = {
            "step": 0,
            "user_data": {},
            "awaiting_confirmation": False,
            "started": False,
            "correction_mode": False
        }

    state = sessions[session_id]

    detected_intent = None
    detected_entities = {}

    if message:
        try:
            detected_intent, detected_entities = extract_clu_result(message)
            detected_entities = fix_name_entities(message, detected_entities)
        except Exception as e:
            print("CLU error:", e)

    print("MESSAGE:", message)
    print("CLU INTENT:", detected_intent)
    print("CLU ENTITIES:", detected_entities)

    if is_intent(detected_intent, "Help"):
        return jsonify({
            "reply": (
                "Ich helfe dir bei der Benutzerregistrierung. "
                "Du kannst die Angaben einzeln nennen oder mehrere Informationen in einem Satz geben. "
                "Zum Beispiel: Mein Name ist Max Mustermann und ich wohne in Berlin."
            )
        })

    if is_intent(detected_intent, "CancelRegistration"):
        del sessions[session_id]
        return jsonify({
            "reply": "Die Registrierung wurde abgebrochen. Du kannst jederzeit neu starten."
        })

    if is_intent(detected_intent, "RestartRegistration"):
        sessions[session_id] = {
            "step": 0,
            "user_data": {},
            "awaiting_confirmation": False,
            "started": True,
            "correction_mode": False
        }
        return jsonify({"reply": FIELDS[0][1], "display_message": display_message})

    if is_intent(detected_intent, "StartRegistration"):
        state["started"] = True
        return jsonify({"reply": get_next_question_or_summary(state)})

    if state["awaiting_confirmation"]:
        message_lower = message.lower().strip()

        if message_lower in CONFIRM_WORDS or is_intent(detected_intent, "ConfirmData"):
            save_user(state["user_data"])
            del sessions[session_id]
            return jsonify({
                "reply": "Vielen Dank. Der Benutzeraccount wurde erfolgreich gespeichert.",
                "display_message": display_message
            })

        if message_lower in CORRECT_WORDS or is_intent(detected_intent, "CorrectData"):
            state["awaiting_confirmation"] = False
            state["correction_mode"] = True

            return jsonify({
                "reply": (
                    "Kein Problem. Nenne mir einfach die korrigierte Angabe. "
                    "Zum Beispiel: Ich heiße Robin Meier oder Meine E-Mail ist robin@example.de."
                ),
                "display_message": display_message
            })

        if is_intent(detected_intent, "CancelRegistration"):
            del sessions[session_id]
            return jsonify({
                "reply": "Die Registrierung wurde abgebrochen. Du kannst jederzeit neu starten.",
                "display_message": display_message
            })

        return jsonify({
            "reply": "Bitte bestätige mit Ja oder nenne mir die korrigierte Angabe.",
            "display_message": display_message
        })
    
    if state.get("correction_mode"):
        applied_fields, rejected_fields, updated_fields, blocked = validate_and_apply_entities(
            state["user_data"],
            detected_entities
        )

        if applied_fields:
            state["correction_mode"] = False
            state["awaiting_confirmation"] = True

            update_text = ""
            if updated_fields:
                readable_fields = ", ".join(
                    get_readable_field_name(field) for field, _ in updated_fields
                )
                update_text = f"Ich habe folgende Angabe aktualisiert: {readable_fields}.\n\n"

            return jsonify({
                "reply": update_text + create_summary(state["user_data"]) + "\n\nSind diese Angaben jetzt korrekt? Bitte bestätige.",
                "display_message": build_display_message(message, applied_fields)
            })

        return jsonify({
            "reply": (
                "Ich konnte daraus keine gültige Änderung erkennen. "
                "Bitte nenne die korrigierte Angabe als ganzen Satz, zum Beispiel: "
                "Meine E-Mail ist robin@example.de."
            ),
            "display_message": display_message
        })

    current_field = get_current_field(state)

    required_field = current_field if state["started"] else None

    applied_fields, rejected_fields, updated_fields, blocked = validate_and_apply_entities(
        state["user_data"],
        detected_entities,
        required_field=required_field
    )

    if blocked:
        normalized_value = normalize_field(
            current_field,
            normalize_value(current_field, message)
        )

        is_valid, error_message = validate_field(current_field, normalized_value)

        return jsonify({
            "reply": error_message + " " + get_retry_question_for_field(current_field),
            "display_message": display_message
        })

    if applied_fields:
        state["started"] = True

        update_text = ""
        if updated_fields:
            readable_fields = ", ".join(
                get_readable_field_name(field) for field, _ in updated_fields
            )
            update_text = f"Ich habe folgende Angabe aktualisiert: {readable_fields}.\n\n"

        return jsonify({
            "reply": update_text + get_next_question_or_summary(state),
            "display_message": build_display_message(message, applied_fields)
        })

    if current_field:
        normalized_value = normalize_field(
            current_field,
            normalize_value(current_field, message)
        )

        is_valid, error_message = validate_field(current_field, normalized_value)

        if is_valid:
            state["user_data"][current_field] = normalized_value
            state["started"] = True

            return jsonify({
                "reply": get_next_question_or_summary(state),
                "display_message": normalized_value
            })

        return jsonify({
            "reply": error_message + " " + get_retry_question_for_field(current_field),
            "display_message": display_message
        })

    if not applied_fields and current_field:
        normalized_value = normalize_field(
            current_field,
            normalize_value(current_field, message)
        )

        is_valid, error_message = validate_field(current_field, normalized_value)

        if is_valid:
            state["user_data"][current_field] = normalized_value
            state["started"] = True

            return jsonify({
                "reply": get_next_question_or_summary(state),
                "display_message": normalized_value
            })

    if not state["started"]:
        return jsonify({
            "reply": "Hallo! Ich bin dein Registrierungsassistent. Du kannst die Registrierung starten oder direkt deine Daten nennen."
        })

    return jsonify({
        "reply": "Ich konnte daraus keine gültige Registrierungsangabe erkennen. " + get_current_question(state)
    })


@app.route("/admin")
def admin():
    search = request.args.get("search", "").strip()

    if search:
        users = search_users(search)
    else:
        users = get_all_users()

    return render_template("admin.html", users=users, search=search)


@app.route("/export/csv")
def export_csv():
    users = get_all_users()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Id", "FirstName", "LastName", "BirthDate", "Email", "Phone",
        "Street", "HouseNumber", "PostalCode", "City", "Country", "CreatedAt"
    ])

    for user in users:
        writer.writerow([
            user.Id, user.FirstName, user.LastName, user.BirthDate,
            user.Email, user.Phone, user.Street, user.HouseNumber,
            user.PostalCode, user.City, user.Country, user.CreatedAt
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"}
    )


@app.route("/export/json")
def export_json():
    users = get_all_users()

    data = []
    for user in users:
        data.append({
            "id": user.Id,
            "first_name": user.FirstName,
            "last_name": user.LastName,
            "birth_date": user.BirthDate,
            "email": user.Email,
            "phone": user.Phone,
            "street": user.Street,
            "house_number": user.HouseNumber,
            "postal_code": user.PostalCode,
            "city": user.City,
            "country": user.Country,
            "created_at": str(user.CreatedAt)
        })

    return Response(
        json.dumps(data, ensure_ascii=False, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=users_export.json"}
    )


@app.route("/export/statistics/pdf")
def export_statistics_pdf():
    stats = get_statistics()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Statistikbericht - Azure Registration Bot")

    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    y -= 40
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, f"Registrierte Benutzer insgesamt: {stats['total_users']}")

    y -= 40
    pdf.drawString(50, y, "Benutzer pro Land:")
    pdf.setFont("Helvetica", 11)

    for country, count in stats["users_by_country"]:
        y -= 20
        pdf.drawString(70, y, f"{country}: {count}")

    y -= 40
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Benutzer pro Stadt:")
    pdf.setFont("Helvetica", 11)

    for city, count in stats["users_by_city"]:
        y -= 20
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 11)
        pdf.drawString(70, y, f"{city}: {count}")

    pdf.save()
    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=statistics_report.pdf"}
    )

@app.route("/speech/token")
def speech_token():
    token, region = get_speech_token()

    return jsonify({
        "token": token,
        "region": region
    })

@app.route("/speech/synthesize", methods=["POST"])
def synthesize_speech():
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({
            "success": False,
            "error": "Kein Text übergeben."
        })

    success = synthesize_speech_to_file(text)

    return jsonify({
        "success": success,
        "audio_url": "/static/bot_response.wav"
    })

def create_summary(user_data):
    return f"""Bitte prüfe deine Angaben:

Vorname: {user_data.get("first_name")}
Nachname: {user_data.get("last_name")}
Geburtsdatum: {user_data.get("birth_date")}
E-Mail: {user_data.get("email")}
Telefonnummer: {user_data.get("phone")}
Straße: {user_data.get("street")} {user_data.get("house_number")}
PLZ / Ort: {user_data.get("postal_code")} {user_data.get("city")}
Land: {user_data.get("country")}"""


def find_next_missing_step(user_data):
    for index, (field_name, _) in enumerate(FIELDS):
        if field_name not in user_data or not user_data[field_name]:
            return index
    return len(FIELDS)


def clean_user_input(value):
    return value.strip().rstrip(".!?;,")

def is_intent(intent, *names):
    if not intent:
        return False
    return intent.lower() in [name.lower() for name in names]


def get_current_field(state):
    step = find_next_missing_step(state["user_data"])
    state["step"] = step

    if step >= len(FIELDS):
        return None

    return FIELDS[step][0]


def get_current_question(state):
    step = find_next_missing_step(state["user_data"])
    state["step"] = step

    if step >= len(FIELDS):
        return ""

    return FIELDS[step][1]


def get_next_question_or_summary(state):
    step = find_next_missing_step(state["user_data"])
    state["step"] = step

    if step >= len(FIELDS):
        state["awaiting_confirmation"] = True
        return create_summary(state["user_data"]) + "\n\nSind diese Angaben korrekt? Bitte bestätige."

    field_name = FIELDS[step][0]
    return get_question_for_missing_field(field_name)


def validate_and_apply_entities(user_data, detected_entities, required_field=None):
    valid_fields = []
    rejected_fields = []
    updated_fields = []

    for field_name, value in detected_entities.items():
        normalized_value = normalize_field(
            field_name,
            normalize_value(field_name, value)
        )

        is_valid, _ = validate_field(field_name, normalized_value)

        if is_valid:
            valid_fields.append((field_name, normalized_value))
        else:
            rejected_fields.append(field_name)

    valid_field_names = [field for field, _ in valid_fields]

    if required_field and valid_fields and required_field not in valid_field_names:
        return [], rejected_fields, [], True

    for field_name, normalized_value in valid_fields:
        old_value = user_data.get(field_name)

        if old_value and old_value != normalized_value:
            updated_fields.append((field_name, normalized_value))

        user_data[field_name] = normalized_value

    return valid_fields, rejected_fields, updated_fields, False


def normalize_value(field_name, value):
    value = clean_user_input(value)

    replacements = [
        "mein vorname ist ",
        "mein nachname ist ",
        "mein name ist ",
        "ich heiße ",
        "ich heisse ",
        "ich wohne in ",
        "ich wohne ",
        "in ",
        "meine e-mail ist ",
        "meine email ist ",
        "meine mail ist ",
        "e-mail ist ",
        "email ist ",
        "mail ist ",
        "meine telefonnummer ist ",
        "meine nummer ist ",
        "telefonnummer ist ",
        "telefon ist ",
        "meine adresse ist ",
        "adresse ist "
    ]

    lowered = value.lower()

    for prefix in replacements:
        if lowered.startswith(prefix):
            value = value[len(prefix):].strip()
            break

    if field_name == "country":
        value = value.replace("In ", "").replace("in ", "").strip()

    return clean_user_input(value)


def fix_name_entities(message, detected_entities):
    message_lower = message.lower()

    if not detected_entities:
        return detected_entities

    if "vorname" in message_lower:
        detected_entities.pop("last_name", None)

    if "nachname" in message_lower:
        detected_entities.pop("first_name", None)

    if (
        "first_name" in detected_entities
        and "last_name" in detected_entities
        and detected_entities["first_name"].lower() == detected_entities["last_name"].lower()
    ):
        detected_entities.pop("last_name", None)

    return detected_entities


def build_display_message(original_message, applied_fields):
    applied = dict(applied_fields)

    address_fields = ["street", "house_number", "postal_code", "city", "country"]

    if any(field in applied for field in address_fields):
        street = applied.get("street", "")
        house_number = applied.get("house_number", "")
        postal_code = applied.get("postal_code", "")
        city = applied.get("city", "")
        country = applied.get("country", "")

        line1 = f"{street} {house_number}".strip()
        line2 = f"{postal_code} {city}".strip()
        line3 = country.strip()

        return ", ".join(part for part in [line1, line2, line3] if part)

    display_values = []

    for field_name, value in applied_fields:
        if field_name in ["birth_date", "email", "phone", "postal_code", "house_number"]:
            display_values.append(value)

    if display_values:
        return ", ".join(display_values)

    return original_message

FIELD_ALIASES = {
    "vorname": "first_name",
    "nachname": "last_name",
    "name": "last_name",
    "geburtsdatum": "birth_date",
    "geburtstag": "birth_date",
    "email": "email",
    "e-mail": "email",
    "mail": "email",
    "telefon": "phone",
    "telefonnummer": "phone",
    "handynummer": "phone",
    "straße": "street",
    "strasse": "street",
    "hausnummer": "house_number",
    "postleitzahl": "postal_code",
    "plz": "postal_code",
    "ort": "city",
    "stadt": "city",
    "land": "country"
}


def detect_correction_field(message):
    message_lower = message.lower()

    for alias, field_name in FIELD_ALIASES.items():
        if alias in message_lower:
            return field_name

    return None

def get_field_question(field_name):
    for field, question in FIELDS:
        if field == field_name:
            return f"Okay, bitte gib den neuen Wert an. {question}"

    return "Welche Angabe möchtest du ändern?"

def get_readable_field_name(field_name):
    names = {
        "first_name": "Vorname",
        "last_name": "Nachname",
        "birth_date": "Geburtsdatum",
        "email": "E-Mail-Adresse",
        "phone": "Telefonnummer",
        "street": "Straße",
        "house_number": "Hausnummer",
        "postal_code": "Postleitzahl",
        "city": "Ort",
        "country": "Land"
    }

    return names.get(field_name, field_name)

def get_question_for_missing_field(field_name):
    if field_name in ["first_name", "last_name"]:
        return "Wie heißt du?"

    if field_name == "birth_date":
        return "Wann wurdest du geboren?"

    if field_name == "email":
        return "Wie lautet deine E-Mail-Adresse?"

    if field_name == "phone":
        return "Wie lautet deine Telefonnummer?"

    if field_name == "street":
        return "Wie lautet deine vollständige Adresse?"

    if field_name == "house_number":
        return "Wie lautet deine Hausnummer?"

    if field_name == "postal_code":
        return "Wie lautet deine Postleitzahl?"

    if field_name == "city":
        return "In welchem Ort wohnst du?"

    if field_name == "country":
        return "In welchem Land wohnst du?"

    return "Bitte gib die fehlende Angabe ein."

def get_retry_question_for_field(field_name):
    if field_name == "email":
        return "Bitte nenne deine E-Mail-Adresse erneut."

    if field_name == "phone":
        return "Bitte nenne deine Telefonnummer erneut."

    if field_name == "birth_date":
        return "Bitte nenne dein Geburtsdatum erneut."

    if field_name == "postal_code":
        return "Bitte nenne deine 5-stellige Postleitzahl."

    if field_name == "house_number":
        return "Bitte nenne deine Hausnummer."

    return get_question_for_missing_field(field_name)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)