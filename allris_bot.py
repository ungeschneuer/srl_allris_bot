import requests
import logging
from mastodon import Mastodon
import os
from dotenv import load_dotenv
import re
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
from typing import List, Dict
import time  # Für Wartezeiten zwischen Posts

load_dotenv()  # Loads variables from .env into the environment


# === Konfiguration ===
ACCESS_TOKEN = os.getenv("MASTODON_ACCESS_TOKEN", "dein_mastodon_token")
INSTANCE_URL = os.getenv("MASTODON_INSTANCE_URL", "https://gruene.social")
LAST_ID_FILE = "last_posted_id.txt"
LOG_FILE = "bot.log"
DATA_URL = "https://ratsinformation.leipzig.de/allris_leipzig_public/oparl/papers"

# === Standardwerte für fehlende Daten ===
DEFAULT_TITLE = "Kein Titel"
DEFAULT_TYPE = "Unbekannt"
DEFAULT_WEB_LINK = "Keine URL"
DEFAULT_REFERENCE = "Keine Referenz"
DEFAULT_ACCESS_URL = "Keine URL"

# === Logging einrichten ===
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# === Mastodon-Client initialisieren ===
mastodon = Mastodon(
    access_token=ACCESS_TOKEN,
    api_base_url=INSTANCE_URL
)

# === Hilfsfunktionen ===

def load_last_id() -> int:
    """
    Lädt die zuletzt gepostete ID aus einer Datei.
    Gibt 0 zurück, wenn die Datei nicht existiert.
    """
    logging.info("Versuche, die zuletzt gepostete ID zu laden.")
    if not os.path.exists(LAST_ID_FILE):
        logging.warning(f"Datei {LAST_ID_FILE} existiert nicht. Setze ID auf 0.")
        return 0
    try:
        with open(LAST_ID_FILE, "r") as f:
            last_id = int(f.read().strip())
            logging.info(f"Erfolgreich geladen: Letzte ID ist {last_id}.")
            return last_id
    except Exception as e:
        logging.error(f"Fehler beim Laden der letzten ID: {e}")
        return 0


def save_last_id(last_id: int) -> None:
    """
    Speichert die zuletzt gepostete ID in einer Datei.
    """
    logging.info(f"Speichere die letzte gepostete ID: {last_id}.")
    try:
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(last_id))
        logging.info("ID erfolgreich gespeichert.")
    except Exception as e:
        logging.error(f"Fehler beim Speichern der letzten ID: {e}")


def extract_id(paper_url: str) -> int:
    """
    Extrahiert die ID aus der URL eines Papiers.
    Gibt 0 zurück, wenn die ID nicht extrahiert werden kann.
    """
    logging.info(f"Extrahiere ID aus URL: {paper_url}")
    try:
        parsed = urlparse(paper_url)
        query = parse_qs(parsed.query)
        paper_id = int(query.get("id", [0])[0])
        logging.info(f"Erfolgreich extrahiert: ID ist {paper_id}.")
        return paper_id
    except Exception as e:
        logging.error(f"Fehler beim Extrahieren der ID aus {paper_url}: {e}")
        return 0


def get_recent_papers() -> List[Dict]:
    """
    Ruft die neuesten Papiere aus der API ab, die in den letzten 24 Stunden erstellt wurden.
    Gibt eine Liste von Papier-Dictionaries zurück.
    """
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    url = f"{DATA_URL}/papers?filter[created]={yesterday}"
    logging.info(f"Rufe aktuelle Papiere von {url} ab.")
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        papers = data.get("data", [])
        logging.info(f"Erfolgreich {len(papers)} Papiere abgerufen.")
        return papers
    except requests.RequestException as e:
        logging.error(f"Fehler beim Abrufen der Daten: {e}")
        return []


def create_status(paper: Dict) -> str:
    """
    Erstellt den Status-String für einen Mastodon-Post basierend auf den Papierdaten.
    Nur verfügbare Informationen werden in den Status aufgenommen.
    """
    logging.info(f"Erstelle Status für Papier: {paper.get('name', DEFAULT_TITLE)}")

    # Titel
    title = paper.get("name", DEFAULT_TITLE)
    status_lines = [f"🗂️ Titel: \"{title}\""]

    # Typ
    paper_type = paper.get("paperType")
    if paper_type:
        status_lines.append(f"📄 Typ: {paper_type}")

    # Erstellungsdatum
    created_at_raw = paper.get("created")
    if created_at_raw:
        try:
            created_at = datetime.fromisoformat(created_at_raw).strftime("%d.%m.%Y %H:%M")
            status_lines.append(f"📅 Bereitgestellt am: {created_at}")
        except ValueError:
            logging.warning(f"Ungültiges Erstellungsdatum: {created_at_raw}")

    # ALLRIS-Link
    web_link = paper.get("web")
    if web_link:
        status_lines.append(f"🔗 ALLRIS: {web_link}")

    # PDF-Link
    access_url = paper.get("mainFile", {}).get("accessUrl")
    if access_url:
        status_lines.append(f"🌐 PDF: {access_url}")

    # Hashtags
    status_lines.append("#leipzig #leipzigerstadtrat")

    # Status zusammenfügen
    status = "\n".join(status_lines)
    logging.info(f"Status erfolgreich erstellt: {status}")
    return status

# === Hauptfunktion ===

def check_and_post_new_papers() -> None:
    """
    Überprüft und postet neue Papiere auf Mastodon.
    Nur Papiere mit einer ID größer als die zuletzt gespeicherte ID werden gepostet.
    Zwischen jedem Post wird eine Minute gewartet.
    """
    logging.info("Starte Überprüfung und Posting neuer Papiere.")
    try:
        papers = get_recent_papers()
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Daten: {e}")
        return

    last_posted_id = load_last_id()
    new_papers = []

    # Filtere Papiere mit einer ID größer als der zuletzt gespeicherten ID
    for paper in papers:
        paper_id = extract_id(paper.get("id", ""))
        if paper_id <= last_posted_id:
            logging.info(f"Überspringe Papier mit ID {paper_id}, da es bereits gepostet wurde.")
            continue
        new_papers.append((paper_id, paper))

    # Sortiere die Papiere nach ID aufsteigend
    new_papers.sort()
    logging.info(f"{len(new_papers)} neue Papiere zum Posten gefunden.")

    # Poste jedes neue Papier
    for paper_id, paper in new_papers:
        status = create_status(paper)

        try:
            logging.info(f"Poste Papier mit ID {paper_id}.")
            mastodon.toot(status)
            save_last_id(paper_id)
            logging.info(f"Erfolgreich gepostet: {paper.get('name', DEFAULT_TITLE)} (ID: {paper_id})")
        except Exception as e:
            logging.error(f"Fehler beim Posten von Papier mit ID {paper_id}: {e}")

        # Wartezeit von 1 Minute zwischen den Posts
        logging.info("Warte 60 Sekunden vor dem nächsten Post.")
        time.sleep(60)

# === Testfunktion ===

def test_print_posts() -> None:
    """
    Testet die Erstellung von Status-Strings für Papiere, ohne sie zu posten.
    """
    logging.info("Starte Testfunktion: test_print_posts")
    try:
        recent_papers = get_recent_papers()
        last_id = load_last_id()
        logging.info(f"Anzahl der abgerufenen Papiere: {len(recent_papers)}")
        logging.info(f"Letzte gespeicherte ID: {last_id}")
        
        for paper in recent_papers:
            paper_id = extract_id(paper.get("id", ""))
            status = create_status(paper)

            logging.info(f"Test-Post für Papier-ID {paper_id}: {paper.get('name', DEFAULT_TITLE)}")
            print("=== TEST POST ===")
            print(status)
            print("=================\n")
    except Exception as e:
        logging.error(f"Fehler in test_print_posts: {e}")


if __name__ == "__main__":
    logging.info("Bot gestartet.")
    check_and_post_new_papers()
    logging.info("Bot beendet.")