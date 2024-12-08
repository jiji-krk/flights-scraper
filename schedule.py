name: Update Flight Data Hourly

on:
  schedule:
    - cron: "0 * * * *"  # Exécuter toutes les heures
  workflow_dispatch:  # Permet d'exécuter manuellement

jobs:
  update-database:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Download previous database artifact
        uses: actions/download-artifact@v3
        with:
          name: flights-database  # Nom de l'artefact précédent
          path: flights_data.db

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install selenium pandas

      - name: Run scraping script
        run: python schedule.py  # Exécute le script pour mettre à jour la base

      - name: Check if database exists
        run: ls -l flights_data.db  # Vérifie si la base SQLite existe

      - name: Upload SQLite database
        uses: actions/upload-artifact@v3
        with:
          name: flights-database
          path: flights_data.db
