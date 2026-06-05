# Azure Registration Bot

## Projektbeschreibung

Dieses Projekt ist ein cloudbasierter Registrierungsbot für das Modul **Advanced Topics in Cloud Computing**. Der Bot führt Benutzer durch einen Registrierungsprozess, erkennt Benutzerdaten teilweise über Azure Conversational Language Understanding, validiert Eingaben und speichert die Daten in einer Azure SQL Database.

## Funktionen

- Webbasierte Chat-Oberfläche
- Schrittweise Benutzerregistrierung
- Verarbeitung natürlicher Sprache über Azure Conversational Language Understanding
- Erfassung von persönlichen Daten, Kontaktdaten und Adressdaten
- Validierung von E-Mail, Telefonnummer, Geburtsdatum und Postleitzahl
- Speicherung der Daten in Azure SQL Database
- Administrator-Dashboard zur Anzeige gespeicherter Benutzer
- Suchfunktion nach Name, E-Mail, Ort und PLZ
- CSV-Export
- JSON-Export
- PDF-Statistikbericht

## Technologien

- Python
- Flask
- Azure App Service
- Azure SQL Database
- Azure AI Language / Conversational Language Understanding
- pyodbc
- requests
- reportlab
- HTML/CSS/JavaScript
- GitHub
- GitHub Actions

## Architektur

Benutzer  
→ Flask Web-Chat auf Azure App Service  
→ Dialoglogik und Validierung  
→ Azure Conversational Language Understanding  
→ Azure SQL Database  
→ Admin-Dashboard / Exporte / Statistik

## Installation

```bash
pip install -r requirements.txt