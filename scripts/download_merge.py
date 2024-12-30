#!/usr/bin/env python3

import os
import requests
import zipfile
import sqlite3
import tempfile
from urllib.parse import urljoin


GITHUB_TOKEN = os.environ.get("GH_PAT")

OWNER = "jiji-krk"
REPO = "flights-scraper"
ARTIFACT_NAME = "flights-database"
BASE_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/artifacts"


# Fichier final dans lequel on fusionnera tout
MERGED_DB = "merged_flights.db"
TABLE_NAME = "flights"  # Table que vous allez fusionner


def list_artifacts(per_page=100):
    """
    Récupère toutes les pages d'artifacts depuis l'API GitHub.
    Retourne la liste complète d'objets JSON correspondants.
    """
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    page = 1
    artifacts = []
    while True:
        url = f"{BASE_URL}?per_page={per_page}&page={page}"
        print(f"Fetching page {page} -> {url}")
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()

        data = resp.json()
        items = data.get("artifacts", [])
        artifacts.extend(items)

        # Vérifier si on a récupéré toutes les pages
        if len(items) < per_page:
            break
        page += 1

    return artifacts

def download_artifact_zip(artifact):
    """
    Télécharge l'archive d'un artifact (ZIP) dans un fichier temporaire,
    renvoie le chemin du .zip.
    """
    artifact_id = artifact["id"]
    download_url = artifact["archive_download_url"]

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    # Fichier zip temporaire
    tmp_zip_path = os.path.join(tempfile.gettempdir(), f"artifact_{artifact_id}.zip")

    print(f"Downloading artifact {artifact_id} to {tmp_zip_path}")
    r = requests.get(download_url, headers=headers, stream=True)
    r.raise_for_status()

    with open(tmp_zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    return tmp_zip_path

def extract_sqlite_db(zip_path, output_dir="."):
    """
    Extrait le contenu du zip dans 'output_dir'.
    Retourne la liste des fichiers extraits (souvent un seul).
    """
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(output_dir)
        return z.namelist()

def merge_sqlite_db(source_db_path, dest_db_path):
    print(f"Merging data from {source_db_path} into {dest_db_path}")
    with sqlite3.connect(dest_db_path) as conn_dest:
        with sqlite3.connect(source_db_path) as conn_src:
            conn_src.row_factory = sqlite3.Row
            src_cursor = conn_src.cursor()

            src_cursor.execute(f"""
                SELECT
                  "Out Duration"   AS out_duration,
                  "Return Duration" AS return_duration,
                  "Out Time"       AS out_time,
                  "Return Time"    AS return_time,
                  "Out Stops"      AS out_stops,
                  "Out Airline"    AS out_airline,
                  Price            AS price,
                  "Scraped TimeStamp"   AS scraped_time
                FROM {TABLE_NAME}
            """)
            rows = src_cursor.fetchall()

        dest_cursor = conn_dest.cursor()

        dest_cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                out_duration     TEXT,
                return_duration  TEXT,
                out_time         TEXT,
                return_time      TEXT,
                out_stops        TEXT,
                out_airline      TEXT,
                price            REAL,
                scraped_time     TEXT
            )
        """)

        # On insère les valeurs (alias) dans la DB de destination
        for row in rows:
            dest_cursor.execute(f"""
                INSERT OR IGNORE INTO {TABLE_NAME} (
                    out_duration,
                    return_duration,
                    out_time,
                    return_time,
                    out_stops,
                    out_airline,
                    price,
                    scraped_time
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["out_duration"],
                row["return_duration"],
                row["out_time"],
                row["return_time"],
                row["out_stops"],
                row["out_airline"],
                row["price"],
                row["scraped_time"]
            ))

        conn_dest.commit()


def main():
    if not GITHUB_TOKEN or GITHUB_TOKEN.startswith("REPLACE_WITH"):
        print("Veuillez définir la variable d'environnement GH_PAT avec un PAT GitHub.")
        return

    # 1) Lister tous les artifacts
    all_artifacts = list_artifacts()
    print(f"Found {len(all_artifacts)} total artifacts in {OWNER}/{REPO}.")

    # 2) Filtrer uniquement ceux qui s'appellent "flights-database" et ne sont pas expirés
    db_artifacts = [a for a in all_artifacts
                    if a["name"] == ARTIFACT_NAME and not a["expired"]]

    print(f"Found {len(db_artifacts)} artifacts named {ARTIFACT_NAME} (non-expired).")

    # 3) Créer le fichier DB final s'il n'existe pas
    if not os.path.isfile(MERGED_DB):
        print(f"Creating empty {MERGED_DB} ...")
        with sqlite3.connect(MERGED_DB) as conn:
            pass

    # 4) Télécharger et fusionner
    for artifact in db_artifacts:
        zip_path = download_artifact_zip(artifact)

        extracted_files = extract_sqlite_db(zip_path, output_dir="tmp_extracted")
        for f in extracted_files:
            if f.endswith(".db"):
                source_db_path = os.path.join("tmp_extracted", f)
                merge_sqlite_db(source_db_path, MERGED_DB)

        os.remove(zip_path)
        # Supprimer le .db temporaire

    print("All done. The merged DB is:", MERGED_DB)

if __name__ == "__main__":
    main()
