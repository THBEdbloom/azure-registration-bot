import re
from datetime import datetime


def validate_required(value):
    return value.strip() != ""


def validate_birth_date(value):
    try:
        birth = datetime.strptime(value, "%d.%m.%Y")

        if birth > datetime.now():
            return False

        return True

    except ValueError:
        return False


def validate_email(value):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, value) is not None


def validate_phone(value):
    digits = re.sub(r"\D", "", value)
    return len(digits) >= 6


def validate_postal_code(value):
    pattern = r"^[A-Za-z0-9\- ]{4,10}$"
    return re.match(pattern, value) is not None


def validate_name(value):
    pattern = r"^[A-Za-zÄÖÜäöüß\- ]+$"
    return re.match(pattern, value) is not None


def validate_field(field_name, value):

    if not validate_required(value):
        return False, "Diese Angabe darf nicht leer sein."

    if field_name in ["first_name", "last_name"]:
        if not validate_name(value):
            return False, "Bitte gib einen gültigen Namen ein."

    if field_name == "birth_date":
        if not validate_birth_date(value):
            return False, "Bitte gib ein gültiges Geburtsdatum im Format TT.MM.JJJJ ein."

    if field_name == "email":
        if not validate_email(value):
            return False, "Bitte gib eine gültige E-Mail-Adresse ein, z.B. max.mustermann@example.de."

    if field_name == "phone":
        if not validate_phone(value):
            return False, "Bitte gib eine gültige Telefonnummer ein, z.B. +49 151 12345678."

    if field_name == "postal_code":
        if not validate_postal_code(value):
            return False, "Bitte gib eine gültige Postleitzahl ein."

    return True, ""