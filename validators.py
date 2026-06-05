import re
from datetime import datetime


def validate_birth_date(value):
    try:
        datetime.strptime(value, "%d.%m.%Y")
        return True
    except ValueError:
        return False


def validate_email(value):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, value) is not None


def validate_phone(value):
    pattern = r"^[0-9+\-\s/()]+$"
    return re.match(pattern, value) is not None and len(value) >= 5


def validate_postal_code(value):
    return value.isdigit() and len(value) == 5


def validate_required(value):
    return value.strip() != ""


def validate_field(field_name, value):
    if not validate_required(value):
        return False, "Diese Angabe darf nicht leer sein."

    if field_name == "birth_date" and not validate_birth_date(value):
        return False, "Bitte gib das Geburtsdatum im Format TT.MM.JJJJ ein, z.B. 01.01.2000."

    if field_name == "email" and not validate_email(value):
        return False, "Bitte gib eine gültige E-Mail-Adresse ein, z.B. max.mustermann@example.de."

    if field_name == "phone" and not validate_phone(value):
        return False, "Bitte gib eine gültige Telefonnummer ein, z.B. +49 151 12345678."

    if field_name == "postal_code" and not validate_postal_code(value):
        return False, "Bitte gib eine gültige 5-stellige Postleitzahl ein."

    return True, ""