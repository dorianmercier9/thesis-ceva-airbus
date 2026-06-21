"""
init_db.py
Script d'initialisation de la base de données SQLite.
À exécuter UNE SEULE FOIS avant le premier lancement de l'application.

Emplacement : thesis_ceva/scripts/init_db.py
Exécution   : python3 scripts/init_db.py (depuis le dossier thesis_ceva)
"""

import sqlite3
import os
from pathlib import Path

# Chemin vers la base de données
DB_PATH = Path(__file__).parent.parent / "app" / "data" / "ceva_analytics.db"

def init_database():
    print(f"Initialisation de la base de données...")
    print(f"Emplacement : {DB_PATH}")

    os.makedirs(DB_PATH.parent, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ── TABLE : analyses ─────────────────────────────────────────────────────
    # Historique de chaque analyse lancée depuis l'application
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date_analyse    TEXT NOT NULL,
            periode_debut   TEXT,
            periode_fin     TEXT,
            total           INTEGER,
            ignored         INTEGER DEFAULT 0
        )
    """)

    # ── TABLE : resultats ────────────────────────────────────────────────────
    # Une ligne par expédition analysée, liée à une analyse
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resultats (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            analyse_id          INTEGER NOT NULL,
            shipment_id         TEXT,
            customer_reference  TEXT,
            route               TEXT,
            carrier_name        TEXT,
            business_unit       TEXT,
            pickup_date         TEXT,
            lead_time           INTEGER,
            score_risque        REAL,
            rang                INTEGER,
            priorite            TEXT,
            rang_relatif        TEXT,
            FOREIGN KEY (analyse_id) REFERENCES analyses(id)
        )
    """)

    # ── TABLE : suivis ───────────────────────────────────────────────────────
    # Expéditions marquées comme traitées par l'équipe Performance
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS suivis (
            shipment_id     TEXT PRIMARY KEY,
            pickup_date     TEXT NOT NULL,
            marked_at       TEXT NOT NULL,
            active          INTEGER DEFAULT 1
        )
    """)

    # ── TABLE : unknown_elements ─────────────────────────────────────────────
    # Éléments non reconnus détectés lors des analyses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS unknown_elements (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            type            TEXT NOT NULL,
            valeur          TEXT NOT NULL,
            shipment_id     TEXT NOT NULL,
            detected_at     TEXT NOT NULL,
            UNIQUE(type, valeur, shipment_id)
        )
    """)

    conn.commit()
    conn.close()

    print("Base de données initialisée avec succès.")
    print("Tables créées : analyses, resultats, suivis, unknown_elements")

if __name__ == "__main__":
    init_database()
