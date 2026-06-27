# CEVA Logistics — Système de Prédiction des Retards Aériens
### Projet annuel Master 2 Data & IA — Dorian Mercier

---

## Présentation

Ce projet est un système de prédiction des risques de retard sur les expéditions aériennes du contrat Airbus, développé dans le cadre du Master 2 Data & IA (IA School / Nexa Business School).

Il se compose d'un modèle de machine learning (Random Forest) entraîné sur environ 16 000 expéditions synthétiques représentatives des flux réels, et d'une application web Streamlit permettant à l'équipe Performance de CEVA Logistics de prioriser ses interventions préventives au quotidien.

**URL publique** : https://thesis-ceva-airbus-tuxrdhznfvadajonktddvm.streamlit.app/

**Dépôt Git** : https://github.com/dorianmercier9/thesis-ceva-airbus

---

## Structure du projet

```
thesis_ceva/
├── app/
│   ├── app_final.py              Application Streamlit
│   └── data/
│       ├── carrier_full_stats.json    Statistiques historiques par transporteur
│       ├── route_full_stats.json      Statistiques historiques par route
│       └── ceva_analytics.db         Base SQLite (créée automatiquement au démarrage)
├── models/
│   ├── random_forest_corrected.pkl    Modèle Random Forest entraîné
│   ├── scaler_corrected.pkl           Scaler de normalisation
│   └── metrics_corrected.pkl          Métriques de performance du modèle
├── notebooks/
│   ├── 01_EDA.ipynb                   Analyse exploratoire des données
│   └── 02_Modeling_CORRECTED.ipynb    Modélisation et entraînement
├── data/
│   └── raw/
│       └── raw_shipments_full.csv     Dataset synthétique source (40 801 lignes)
├── scripts/
│   ├── generate_raw_data.py           Génération du dataset synthétique
│   ├── clean_and_filter_AIR.py        Nettoyage et filtrage sur le mode aérien
│   └── init_db.py                     Initialisation manuelle de la base SQLite
├── docs/
│   └── Data_Dictionary.xlsx           Dictionnaire des variables
├── README.md
└── requirements.txt
```

---

## Prérequis

- Python 3.9 ou supérieur
- pip

---

## Installation

**1. Cloner le dépôt**

```bash
git clone https://github.com/dorianmercier9/thesis-ceva-airbus.git
cd thesis-ceva-airbus
```

**2. Installer les dépendances**

```bash
pip install -r requirements.txt
```

**3. Lancer l'application**

```bash
streamlit run app/app_final.py
```

La base de données SQLite est créée automatiquement au premier démarrage dans `app/data/ceva_analytics.db`. Aucune configuration supplémentaire n'est requise.

---

## Fichier de test

Un fichier de démonstration est disponible pour tester l'application :

```
data/demo/test_demo_final.csv
```

Ce fichier contient 300 expéditions planifiées sur des routes et transporteurs du référentiel, avec une date de pickup dans la fenêtre J+1 à J+30. Il inclut un transporteur non reconnu (`Nordic Air Cargo`) et deux routes non reconnues (`ES→FR`, `TK→JP`) pour illustrer le mécanisme de détection des éléments inconnus.

**Étapes de test :**
1. Ouvrir l'application dans le navigateur
2. Page **Analyse** → charger `test_demo_final.csv`
3. Cliquer **Lancer l'analyse**
4. Vérifier le classement Top 50, marquer des expéditions comme traitées
5. Page **Vue analytique** → consulter la répartition par carrier et par route
6. Page **Documentation** → vérifier les éléments non reconnus détectés

---

## Architecture des données

L'application repose sur une base SQLite légère (`ceva_analytics.db`) composée de quatre tables :

| Table | Contenu |
|-------|---------|
| `analyses` | Historique de chaque analyse lancée (date, période, volume) |
| `resultats` | Expéditions analysées avec score de risque, rang et priorité |
| `suivis` | Expéditions marquées comme traitées par l'équipe Performance |
| `unknown_elements` | Transporteurs et routes non reconnus détectés par Shipment_ID unique |

Ce choix architectural est adapté à la phase de démonstration. En production, une migration vers PostgreSQL ou SQL Server permettrait la gestion multi-utilisateurs simultanés et l'intégration au système d'information CEVA existant.

**Export SQL de la base :**

```bash
sqlite3 app/data/ceva_analytics.db .dump > ceva_analytics_dump.sql
```

---

## Compatibilité navigateur

L'application a été testée et validée sur :
- Google Chrome (recommandé)
- Mozilla Firefox
- Safari

---

## Performances du modèle

| Métrique | Valeur |
|----------|--------|
| Precision Top 50 | 67.7% |
| Recall Top 50 | 42.2% |
| Precision seuil 0.5 | 60.6% |
| Recall seuil 0.5 | 61.4% |
| Dataset d'entraînement | ~16 000 expéditions aériennes |

---

## Reproduire l'entraînement

Pour régénérer le dataset et réentraîner le modèle depuis zéro :

```bash
# 1. Générer le dataset synthétique
python3 scripts/generate_raw_data.py

# 2. Nettoyer et filtrer sur le mode aérien
python3 scripts/clean_and_filter_AIR.py

# 3. Exécuter les notebooks dans l'ordre
# notebooks/01_EDA.ipynb
# notebooks/02_Modeling_CORRECTED.ipynb
```

---

## Contact

Dorian Mercier — Master 2 Data & IA, IA School / Nexa Business School
