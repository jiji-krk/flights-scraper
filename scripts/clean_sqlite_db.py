#!/usr/bin/env python3

import sqlite3
import csv

DB_PATH = "merged_flights.db"
TABLE_NAME = "flights"
OUTPUT_CSV = "artifacts_flights_cleaned.csv"

def main():
    # 1) Se connecter à la base SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 2) Supprimer les lignes pour lesquelles AU MOINS UNE colonne est vide ou NULL
    #    => utilisation de OR
    delete_query = f"""
        DELETE FROM {TABLE_NAME}
        WHERE
            out_duration   IS NULL OR out_duration   = '' OR
            return_duration IS NULL OR return_duration = '' OR
            out_time       IS NULL OR out_time       = '' OR
            return_time    IS NULL OR return_time    = '' OR
            out_stops      IS NULL OR out_stops      = '' OR
            out_airline    IS NULL OR out_airline    = '' OR
            price          IS NULL OR price          = '' OR
            scraped_time   IS NULL OR scraped_time   = ''
    """
    cursor.execute(delete_query)
    deleted_rows = cursor.rowcount
    print(f"Supprimé {deleted_rows} ligne(s) où au moins une colonne était vide/NULL.")

    conn.commit()

    # 3) Exporter la table nettoyée en CSV
    select_query = f"SELECT * FROM {TABLE_NAME}"
    cursor.execute(select_query)
    rows = cursor.fetchall()

    # Récupérer le nom des colonnes
    col_names = [desc[0] for desc in cursor.description]

    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Écrire l'entête
        writer.writerow(col_names)
        # Écrire les données
        for row in rows:
            writer.writerow(row)

    print(f"Export terminé : {OUTPUT_CSV}")

    # 4) Fermer la connexion
    conn.close()


if __name__ == "__main__":
    main()
