from flask import Flask, render_template, request, jsonify
from database import init_db, save_user, get_all_users
from validators import validate_field

app = Flask(__name__)
app.secret_key = "dev-secret-key"

# Reihenfolge des Registrierungsdialogs
FIELDS = [
    ("first_name", "Wie lautet dein Vorname?"),
    ("last_name", "Wie lautet dein Nachname?"),
    ("birth_date", "Wann wurdest du geboren? Bitte im Format TT.MM.JJJJ."),
    ("email", "Wie lautet deine E-Mail-Adresse?"),
    ("phone", "Wie lautet deine Telefonnummer?"),
    ("street", "Wie lautet deine Straße?"),
    ("house_number", "Wie lautet deine Hausnummer?"),
    ("postal_code", "Wie lautet deine Postleitzahl?"),
    ("city", "In welchem Ort wohnst du?"),
    ("country", "In welchem Land wohnst du?")
]

sessions = {}


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    session_id = data.get("session_id", "default")
    message = data.get("message", "").strip()

    if session_id not in sessions:
        sessions[session_id] = {
            "step": 0,
            "user_data": {},
            "awaiting_confirmation": False
        }
        return jsonify({
            "reply": "Hallo! Ich helfe dir bei der Benutzerregistrierung. " + FIELDS[0][1]
        })

    state = sessions[session_id]

    if state["awaiting_confirmation"]:
        if message.lower() in ["ja", "j", "yes"]:
            save_user(state["user_data"])
            del sessions[session_id]
            return jsonify({
                "reply": "Vielen Dank. Der Benutzeraccount wurde erfolgreich gespeichert."
            })
        else:
            del sessions[session_id]
            return jsonify({
                "reply": "Die Registrierung wurde abgebrochen. Starte neu, wenn du möchtest."
            })

    current_step = state["step"]
    field_name, question = FIELDS[current_step]

    is_valid, error_message = validate_field(field_name, message)

    if not is_valid:
        return jsonify({
            "reply": error_message + " " + question
        })

    state["user_data"][field_name] = message
    state["step"] += 1


    if state["step"] < len(FIELDS):
        next_question = FIELDS[state["step"]][1]
        return jsonify({"reply": next_question})

    summary = create_summary(state["user_data"])
    state["awaiting_confirmation"] = True

    return jsonify({
        "reply": summary + "\n\nSind diese Angaben korrekt? Bitte antworte mit Ja oder Nein."
    })


@app.route("/admin")
def admin():
    users = get_all_users()
    return render_template("admin.html", users=users)


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


if __name__ == "__main__":
    init_db()
    app.run(debug=True)