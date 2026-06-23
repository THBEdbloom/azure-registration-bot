# Azure Registration Bot

## Projektbeschreibung

Der Azure Registration Bot ist ein sprach- und textbasierter Chatbot zur Erfassung und Verwaltung von Benutzerdaten. Der Bot führt Nutzer durch einen vollständigen Registrierungsprozess, validiert die eingegebenen Daten und speichert diese in einer Azure SQL Database.

Die Anwendung unterstützt sowohl die Interaktion über einen Webchat als auch über Spracheingabe und Sprachausgabe mittels Azure Speech Services.

---

# Funktionen

## Benutzerregistrierung

Der Bot erfasst folgende Daten:

### Persönliche Daten

* Vorname
* Nachname
* Geburtsdatum

### Kontaktdaten

* E-Mail-Adresse
* Telefonnummer

### Adressdaten

* Straße
* Hausnummer
* Postleitzahl
* Ort
* Land

Passwörter werden bewusst nicht erfasst.

---

## Dialogfunktionen

* Geführter Registrierungsprozess
* Kontextbezogene Nachfragen
* Hilfe-Funktion
* Korrektur von Daten
* Abbruch und Neustart der Registrierung
* Validierung aller Eingaben
* Fehlertolerante Verarbeitung von Spracheingaben

---

## Administration

* Übersicht aller registrierten Benutzer
* Suchfunktion
* CSV-Export
* JSON-Export
* PDF-Statistikbericht

---

# Verwendete Azure-Dienste

## Azure Bot Service

Bereitstellung des Bots für verschiedene Kommunikationskanäle.

## Azure Speech Services

* Spracheingabe (Speech-to-Text)
* Sprachausgabe (Text-to-Speech)

## Azure Conversational Language Understanding (CLU)

Erkennung von:

* Intents
* Entitäten
* Benutzerdaten

## Azure SQL Database

Speicherung aller Registrierungsdaten.

## Azure App Service

Hosting der Anwendung.

## Azure Key Vault

Verwaltung sensibler Konfigurationsdaten und Zugangsdaten.

---

# Systemarchitektur

Die Anwendung ist in mehrere Schichten unterteilt.

## Präsentationsschicht

### Weboberfläche

* Chat-Interface
* Sprachsteuerung
* Administrator-Dashboard

## Geschäftslogik

### Dialog Service

Verwaltung des Gesprächsablaufs.

### CLU Service

Auswertung von Benutzereingaben.

### Speech Service

Verarbeitung von Spracheingabe und Sprachausgabe.

### Bot Service

Anbindung an den Azure Bot Service.

## Datenzugriff

### User Repository

Zugriff auf die Azure SQL Database.

## Infrastruktur

* Azure App Service
* Azure SQL Database
* Azure Key Vault
* Azure Bot Service
* Azure Speech Services
* Azure CLU

---

# Projektstruktur

```text
azure-registration-bot/

├── .github/
│   └── workflows/

├── repositories/
│   └── user_repository.py

├── services/
│   ├── bot_adapter.py
│   ├── bot_service.py
│   ├── clu_service.py
│   ├── dialog_service.py
│   ├── keyvault_service.py
│   └── speech_service.py

├── templates/
│   ├── admin.html
│   └── chat.html

├── static/
│   └── style.css

├── utils/
│   └── validators.py

├── app.py
├── requirements.txt
└── README.md
```

---

# Ablauf einer Registrierung

1. Benutzer startet die Registrierung.
2. Bot fragt fehlende Daten ab.
3. CLU erkennt Intents und Entitäten.
4. Eingaben werden validiert.
5. Bot zeigt eine Zusammenfassung.
6. Benutzer bestätigt die Daten.
7. Daten werden in Azure SQL gespeichert.
8. Registrierung wird abgeschlossen.

---

# Installation

## Voraussetzungen

* Python 3.10 oder höher
* Azure Subscription
* Azure SQL Database
* Azure Bot Service
* Azure Speech Services
* Azure CLU Projekt
* Azure Key Vault

---

## Repository klonen

```bash
git clone <repository-url>
cd azure-registration-bot
```

---

## Virtuelle Umgebung erstellen

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

---

## Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

---

## Konfiguration

Folgende Einstellungen müssen im Azure App Service oder lokal als Umgebungsvariablen vorhanden sein:

```text
USE_KEY_VAULT=true
KEY_VAULT_URL=<keyvault-url>
```

Die benötigten Secrets werden über Azure Key Vault bereitgestellt.

---

## Anwendung starten

```bash
python app.py
```

Anschließend ist die Anwendung unter

```text
http://localhost:5000
```

erreichbar.

---

# CI/CD

Für die kontinuierliche Integration und Bereitstellung wird GitHub Actions verwendet.

Die Pipeline befindet sich im Verzeichnis:

```text
.github/workflows
```

Bei Änderungen im Repository wird die Anwendung automatisch in Azure bereitgestellt.

https://azure-registration-bot-gnebg6bqefa6fpgz.switzerlandnorth-01.azurewebsites.net/

---

# Skalierbarkeit

Die Anwendung nutzt Azure App Service und Azure SQL Database und kann grundsätzlich horizontal skaliert werden.

Für produktive Umgebungen könnten Sitzungsdaten zusätzlich in einen verteilten Speicher wie Redis ausgelagert werden.

---

# Autor

Laurin Krüger

Technische Hochschule Brandenburg
Azure Registration Bot Projekt
