# Azure Registration Bot

## Projektbeschreibung

Dieses Projekt ist ein Prototyp eines Registrierungsbots für das Modul Advanced Topics in Cloud Computing. Der Bot führt Benutzer schrittweise durch einen Registrierungsprozess, validiert Eingaben und speichert die Daten in einer Azure SQL Database.

## Funktionen

- Webbasierte Chat-Oberfläche
- Schrittweise Benutzerregistrierung
- Erfassung von persönlichen Daten, Kontaktdaten und Adressdaten
- Validierung von E-Mail, Telefonnummer, Geburtsdatum und Postleitzahl
- Speicherung der Daten in Azure SQL Database
- Administrator-Dashboard zur Anzeige gespeicherter Benutzer

## Technologien

- Python
- Flask
- Azure SQL Database
- pyodbc
- HTML/CSS/JavaScript
- GitHub

## Architektur

Benutzer  
→ Flask Web-Chat  
→ Dialoglogik und Validierung  
→ Azure SQL Database  
→ Admin-Dashboard

## Installation

```bash
pip install -r requirements.txt