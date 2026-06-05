import csv
import io
import json
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from database import init_db, save_user, get_all_users, search_users, get_statistics
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

    message_lower = message.lower()

    if message_lower in ["hilfe", "help", "?"]:
        return jsonify({
            "reply": (
                "Ich helfe dir bei der Benutzerregistrierung. "
                "Bitte beantworte die Fragen nacheinander. "
                "Erfasst werden Vorname, Nachname, Geburtsdatum, E-Mail, Telefonnummer und Adresse. "
                "Du kannst jederzeit 'abbrechen' schreiben, um die Registrierung zu beenden."
            )
        })

    if message_lower in ["abbrechen", "cancel", "stop"]:
        if session_id in sessions:
            del sessions[session_id]
        return jsonify({
            "reply": "Die Registrierung wurde abgebrochen. Schreibe eine neue Nachricht, um erneut zu starten."
        })

    if message_lower in ["neu", "neustart", "restart"]:
        if session_id in sessions:
            del sessions[session_id]
        return jsonify({
            "reply": "Der Dialog wurde neu gestartet. Schreibe eine Nachricht, um mit der Registrierung zu beginnen."
        })

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