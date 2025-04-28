# Leipzig ALLRIS Mastodon Bot

Ein Bot, der automatisch Informationen aus dem ALLRIS-System (Allgemeines Ratsinformationssystem) des Leipziger Stadtrats auf Mastodon teilt.

## Funktionen

- Automatisches Abrufen neuer Einträge aus dem ALLRIS-System der Stadt Leipzig
- Veröffentlichung von neuen Vorlagen mit Links zum Original

## Installation

### Voraussetzungen

- Python 3.10.2 oder höher
- Pip (Python-Paketmanager)
- Zugang zu einer Mastodon-Instanz mit API-Schlüssel

### Setup

1. Repository klonen:
   ```
   git clone https://github.com/ungeschneuer/allris_bot.git
   cd allris-bot
   ```

2. Virtuelle Umgebung erstellen und aktivieren:
   ```
   python -m venv venv
   source venv/bin/activate  # Unter Windows: venv\Scripts\activate
   ```

3. Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```

4. Konfigurationsdatei erstellen:
   ```
   cp .env-example .env
   ```

5. Konfigurationsdatei bearbeiten und Mastodon API-Zugangsdaten anpassen.


## Nutzung

### Manueller Start

```
python allris_bot.py
```

### Als Cronjob einrichten

Der Bot kann als Cronjob eingerichtet werden:

```
crontab -e
```

Zum Beispiel: Ausführung alle 2 Stunden
```
0 */2 * * * cd /pfad/zum/bot && /pfad/zum/bot/venv/bin/python /pfad/zum/bot/bot.py
```

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz - siehe [LICENSE](LICENSE.md) für Details.


## Datenschutz und rechtliche Hinweise

- Der Bot verarbeitet ausschließlich öffentlich zugängliche Informationen aus dem ALLRIS-System der Stadt Leipzig.
- Es werden keine personenbezogenen Daten gespeichert, die nicht bereits öffentlich im ALLRIS-System einsehbar sind.
- Dieses Projekt ist keine offizielle Anwendung der Stadt Leipzig.