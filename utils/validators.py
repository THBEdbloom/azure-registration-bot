import re

from datetime import datetime


MONTHS = {
    "januar": "01",
    "februar": "02",
    "märz": "03",
    "maerz": "03",
    "april": "04",
    "mai": "05",
    "juni": "06",
    "juli": "07",
    "august": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "dezember": "12"
}


def normalize_field(
    field_name,
    value
):

    value = value.strip().rstrip(
        ".!?;,"
    )

    if field_name == "birth_date":
        return normalize_birth_date(value)

    if field_name == "email":
        return normalize_email(value)

    if field_name == "phone":
        return normalize_phone(value)

    return value


def normalize_birth_date(value):

    value = value.lower()

    for month, number in MONTHS.items():

        value = value.replace(
            month,
            number
        )

    match = re.search(
        r"(\d{1,2})[\.\s]+(\d{1,2})[\.\s]+(\d{4})",
        value
    )

    if not match:
        return value

    day = match.group(1).zfill(2)
    month = match.group(2).zfill(2)
    year = match.group(3)

    return f"{day}.{month}.{year}"


def normalize_email(value):

    value = value.lower().strip()

    replacements = {
        " at ": "@",
        "ät": "@",
        " ät ": "@",

        " punkt ": ".",
        " dot ": ".",

        " minus ": "-",
        " bindestrich ": "-",

        " unterstrich ": "_",
        " underscore ": "_"
    }

    value = f" {value} "

    for old, new in replacements.items():

        value = value.replace(
            old,
            new
        )

    value = value.strip()

    value = value.replace(
        " ",
        ""
    )

    value = value.replace(
        "(at)",
        "@"
    )

    value = value.replace(
        "[at]",
        "@"
    )

    value = value.replace(
        "{at}",
        "@"
    )

    return value


def normalize_phone(value):

    value = value.strip()

    return re.sub(
        r"[^0-9+]",
        "",
        value
    )


def validate_required(value):

    return value.strip() != ""


def validate_birth_date(value):

    try:

        birth = datetime.strptime(
            value,
            "%d.%m.%Y"
        )

        return birth <= datetime.now()

    except ValueError:

        return False


def validate_email(value):

    pattern = (
        r"^[A-Za-z0-9._%+\-]+"
        r"@[A-Za-z0-9.\-]+"
        r"\.[A-Za-z]{2,}$"
    )

    return (
        re.match(pattern, value)
        is not None
    )


def validate_phone(value):

    pattern = r"^\+?[0-9]{10,15}$"

    return (
        re.match(pattern, value)
        is not None
    )


def validate_postal_code(value):

    return (
        re.match(
            r"^\d{5}$",
            value
        )
        is not None
    )


def validate_name(value):

    pattern = (
        r"^[A-Za-zÄÖÜäöüß\- ]{2,50}$"
    )

    return (
        re.match(
            pattern,
            value.strip()
        )
        is not None
    )


def validate_house_number(value):

    return (
        re.match(
            r"^\d+[a-zA-Z]?$",
            value.strip()
        )
        is not None
    )


def validate_street(value):

    value = value.strip()

    pattern = (
        r"^[A-Za-zÄÖÜäöüß0-9\-\. ]{2,100}$"
    )

    return (
        re.match(pattern, value)
        is not None
        and any(
            char.isalpha()
            for char in value
        )
    )


def validate_city(value):

    pattern = (
        r"^[A-Za-zÄÖÜäöüß\- ]{2,100}$"
    )

    return (
        re.match(
            pattern,
            value.strip()
        )
        is not None
    )


def validate_country(value):

    pattern = (
        r"^[A-Za-zÄÖÜäöüß\- ]{2,100}$"
    )

    return (
        re.match(
            pattern,
            value.strip()
        )
        is not None
    )


VALIDATORS = {
    "first_name": validate_name,
    "last_name": validate_name,
    "birth_date": validate_birth_date,
    "email": validate_email,
    "phone": validate_phone,
    "postal_code": validate_postal_code,
    "house_number": validate_house_number,
    "street": validate_street,
    "city": validate_city,
    "country": validate_country
}


ERROR_MESSAGES = {
    "first_name":
        "Bitte gib einen gültigen Namen ein.",

    "last_name":
        "Bitte gib einen gültigen Namen ein.",

    "birth_date":
        "Bitte gib ein gültiges Geburtsdatum ein, z.B. 20.01.2000 oder 20 Januar 2000.",

    "email":
        "Bitte gib eine gültige E-Mail-Adresse ein, z.B. max.mustermann@example.de.",

    "phone":
        "Bitte gib eine gültige Telefonnummer ein, z.B. +49 151 12345678.",

    "postal_code":
        "Bitte gib eine gültige 5-stellige Postleitzahl ein.",

    "house_number":
        "Bitte gib eine gültige Hausnummer ein, z.B. 12 oder 12a.",

    "street":
        "Bitte gib eine gültige Straße ein.",

    "city":
        "Bitte gib einen gültigen Ort ein.",

    "country":
        "Bitte gib ein gültiges Land ein."
}


def validate_field(
    field_name,
    value
):

    value = normalize_field(
        field_name,
        value
    )

    if not validate_required(value):

        return (
            False,
            "Diese Angabe darf nicht leer sein."
        )

    validator = VALIDATORS.get(
        field_name
    )

    if (
        validator
        and not validator(value)
    ):

        return (
            False,
            ERROR_MESSAGES[field_name]
        )

    return (
        True,
        ""
    )