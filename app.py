from flask import Flask, render_template, request, jsonify, Response

import csv
import io
import json

from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from repositories.user_repository import (
    init_db,
    get_all_users,
    search_users,
    get_statistics
)

from services.dialog_service import (
    handle_chat_message
)

from services.speech_service import (
    get_speech_token,
    synthesize_speech_to_file
)

from services.bot_service import RegistrationBot
from services.bot_adapter import ADAPTER

app = Flask(__name__)
bot = RegistrationBot()
app.secret_key = "dev-secret-key"


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    session_id = data.get(
        "session_id",
        "default"
    )

    message = data.get(
        "message",
        ""
    )

    result = handle_chat_message(
        session_id=session_id,
        message=message
    )

    return jsonify(result)


@app.route("/admin")
def admin():

    search = request.args.get(
        "search",
        ""
    ).strip()

    if search:
        users = search_users(search)

    else:
        users = get_all_users()

    return render_template(
        "admin.html",
        users=users,
        search=search
    )


@app.route("/export/csv")
def export_csv():

    users = get_all_users()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Id",
        "FirstName",
        "LastName",
        "BirthDate",
        "Email",
        "Phone",
        "Street",
        "HouseNumber",
        "PostalCode",
        "City",
        "Country",
        "CreatedAt"
    ])

    for user in users:

        writer.writerow([
            user.Id,
            user.FirstName,
            user.LastName,
            user.BirthDate,
            user.Email,
            user.Phone,
            user.Street,
            user.HouseNumber,
            user.PostalCode,
            user.City,
            user.Country,
            user.CreatedAt
        ])

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment; filename=users_export.csv"
        }
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
            "created_at": str(
                user.CreatedAt
            )
        })

    return Response(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2
        ),
        mimetype="application/json",
        headers={
            "Content-Disposition":
            "attachment; filename=users_export.json"
        }
    )


@app.route("/export/statistics/pdf")
def export_statistics_pdf():

    stats = get_statistics()

    buffer = io.BytesIO()

    pdf = canvas.Canvas(
        buffer,
        pagesize=A4
    )

    width, height = A4

    y = height - 50

    pdf.setFont(
        "Helvetica-Bold",
        16
    )

    pdf.drawString(
        50,
        y,
        "Statistikbericht - Azure Registration Bot"
    )

    y -= 30

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        y,
        f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )

    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        50,
        y,
        f"Registrierte Benutzer insgesamt: {stats['total_users']}"
    )

    y -= 40

    pdf.drawString(
        50,
        y,
        "Benutzer pro Land:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    for country, count in stats["users_by_country"]:

        y -= 20

        pdf.drawString(
            70,
            y,
            f"{country}: {count}"
        )

    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        12
    )

    pdf.drawString(
        50,
        y,
        "Benutzer pro Stadt:"
    )

    pdf.setFont(
        "Helvetica",
        11
    )

    for city, count in stats["users_by_city"]:

        y -= 20

        if y < 50:

            pdf.showPage()

            y = height - 50

            pdf.setFont(
                "Helvetica",
                11
            )

        pdf.drawString(
            70,
            y,
            f"{city}: {count}"
        )

    pdf.save()

    buffer.seek(0)

    return Response(
        buffer.getvalue(),
        mimetype="application/pdf",
        headers={
            "Content-Disposition":
            "attachment; filename=statistics_report.pdf"
        }
    )


@app.route("/speech/token")
def speech_token():

    token, region = get_speech_token()

    return jsonify({
        "token": token,
        "region": region
    })


@app.route(
    "/speech/synthesize",
    methods=["POST"]
)
def synthesize_speech():

    data = request.get_json()

    text = data.get(
        "text",
        ""
    )

    if not text:

        return jsonify({
            "success": False,
            "error": "Kein Text übergeben."
        })

    success = synthesize_speech_to_file(
        text
    )

    return jsonify({
        "success": success,
        "audio_url": "/static/bot_response.wav"
    })


@app.route(
    "/api/messages",
    methods=["POST"]
)
async def messages():

    body = request.json

    auth_header = request.headers.get(
        "Authorization",
        ""
    )

    response = await ADAPTER.process_activity(
        body,
        auth_header,
        bot.on_turn
    )

    if response:
        return jsonify(response.body)

    return "", 200

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )