# 🎓 PLATEFORME PRÉDICTIVE MULTI-MODULES - CEVA LOGISTICS

**Mémoire de Master AI/Data Product Management**  
**Auteur :** Dorian  
**Période :** Mars 2025 - Août 2025  
**Entreprise :** CEVA Logistics (Alternance)

---

## 📋 DESCRIPTION DU PROJET

Développement d'une plateforme ML intégrée pour optimiser les opérations logistiques de CEVA Logistics, appliquée aux Business Units Airbus Civil (AC) et Airbus Defense & Space (ADS).

### 🎯 Objectifs

- **Module 1 : Demand Forecasting** - Prédire les volumes de shipments pour planification ressources
- **Module 2 : Delay Prediction** - Anticiper les retards avant départ pour actions proactives  
- **Module 3 : Operational Intelligence** - Détecter anomalies et scorer performances carriers/routes

### 📊 Dataset

- **31 752 shipments** sur 24 mois (Mars 2023 - Février 2025)
- **35 variables** : Routes, Carriers, MOT, Poids, Dates, Performance, Exceptions
- **Taux retard global** : 33% (ADS: 44%, AC: 26%)

---

## 📁 STRUCTURE DU PROJET

```
thesis_ceva/
├── data/                          # Données
│   ├── raw/                       # Données brutes (CEVA_Data_24months.xlsx)
│   ├── processed/                 # Données nettoyées (train.csv, test.csv)
│   └── external/                  # Données externes (météo, holidays)
│
├── notebooks/                     # Notebooks Jupyter
│   ├── 01_EDA.ipynb              # Analyse exploratoire
│   ├── 02_Module1_Forecasting.ipynb
│   ├── 03_Module2_DelayPrediction.ipynb
│   └── 04_Module3_OpIntelligence.ipynb
│
├── src/                          # Code source Python
│   ├── preprocessing/            # Nettoyage et feature engineering
│   ├── models/                   # Modèles ML
│   ├── visualization/            # Graphiques et viz
│   └── utils/                    # Fonctions utilitaires
│
├── models/                       # Modèles entraînés sauvegardés
│   ├── forecasting/              # SARIMA, Prophet
│   ├── delay_prediction/         # RF, XGBoost classifiers
│   └── operational_intelligence/ # Isolation Forest, scoring
│
├── dashboards/                   # Dashboards Power BI
│   ├── Module1_Forecasting.pbix
│   ├── Module2_DelayPrediction.pbix
│   └── Module3_OpIntelligence.pbix
│
├── outputs/                      # Résultats et exports
│   ├── figures/                  # Graphiques haute résolution
│   ├── reports/                  # Rapports PDF par module
│   └── tables/                   # Tableaux CSV
│
├── docs/                         # Documentation
│   ├── plan/                     # Plan mémoire (60-80 pages)
│   ├── roadmap/                  # Roadmap technique (Mars-Août)
│   └── notes/                    # Notes et recherches
│
├── tracking/                     # Suivi projet
│   └── Suivi_These_CEVA_UPDATED.xlsx (108 tâches)
│
├── requirements.txt              # Dépendances Python
└── README.md                     # Ce fichier
```

---

## 🚀 INSTALLATION & SETUP

### Prérequis

- Python 3.10+
- Jupyter Notebook
- Power BI Desktop

### Installation

```bash
# Cloner le projet (si Git)
git clone <repo_url>
cd thesis_ceva

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt
```

### Dépendances principales

```
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
statsmodels>=0.14.0
prophet>=1.1.0
xgboost>=2.0.0
lightgbm>=4.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.14.0
jupyter>=1.0.0
openpyxl>=3.1.0
```

---

## 📊 UTILISATION

### 1. Analyse Exploratoire (EDA)

```bash
jupyter notebook notebooks/01_EDA.ipynb
```

Génère automatiquement :
- 15-20 visualisations
- Statistiques descriptives
- Insights clés par BU, route, carrier
- Exports CSV

### 2. Module 1 : Forecasting

```bash
jupyter notebook notebooks/02_Module1_Forecasting.ipynb
```

Prédictions hebdomadaires de volumes via SARIMA et Prophet.

### 3. Module 2 : Delay Prediction

```bash
jupyter notebook notebooks/03_Module2_DelayPrediction.ipynb
```

Classification binaire (retard Y/N) + prédiction lead time + exception type.

### 4. Module 3 : Operational Intelligence

```bash
jupyter notebook notebooks/04_Module3_OpIntelligence.ipynb
```

Anomaly detection + carrier scoring + route analysis.

---

## 📈 MÉTRIQUES DE SUCCÈS

### Module 1 (Forecasting)
- ✅ MAPE < 15%
- ✅ RMSE < 100 shipments
- ✅ Prédiction 4 semaines à l'avance

### Module 2 (Delay Prediction)
- ✅ Accuracy > 75%
- ✅ F1-Score > 0.70
- ✅ ROC-AUC > 0.80
- ✅ Lead time RMSE < 3 jours

### Module 3 (Operational Intelligence)
- ✅ Détection anomalies > 80%
- ✅ Faux positifs < 10%
- ✅ Carrier scoring cohérent

---

## 📅 PLANNING

| Phase | Période | Statut |
|-------|---------|--------|
| **Phase 0 : Setup & EDA** | Mars 2025 | 🔄 En cours |
| **Module 1 : Forecasting** | Avril 2025 | ⏳ À faire |
| **Module 2 : Delay Prediction** | Mai 2025 | ⏳ À faire |
| **Module 3 : Op Intelligence** | Juin 2025 | ⏳ À faire |
| **Rédaction Mémoire** | Juillet 2025 | ⏳ À faire |
| **Finalisation & Soutenance** | Août 2025 | ⏳ À faire |

---

## 📝 LIVRABLES

### Techniques
- [x] Dataset semi-fictif 31k lignes
- [x] Notebook EDA complet
- [ ] 3 modèles ML entraînés et sauvegardés
- [ ] 3 dashboards Power BI interactifs
- [ ] Code source documenté et reproductible

### Académiques
- [x] Plan de mémoire détaillé (60-80 pages)
- [x] Roadmap technique (Mars-Août)
- [ ] Mémoire final PDF
- [ ] Slides présentation soutenance (20-25 slides)

---

## 🔍 INSIGHTS CLÉS (EDA)

### Volume & Temporalité
- **31 752** shipments sur 24 mois
- Saisonnalité marquée : pics mai-juin et oct-nov, creux juil-août
- Événements : Mars 2024 (42.7% retards - grève), Décembre (40%+ - rush)

### Business Units
- **AC** (Civil) : 19 121 shipments - **26% retards** - poids moyen 1100 kg
- **ADS** (Defense) : 12 631 shipments - **44% retards** - poids moyen 4000 kg
- ADS : 18% hazardous vs 2% AC

### Routes & Carriers
- Route #1 : **US→FR** (9 448 shipments)
- Route la plus problématique : **ES→TR** (48.5% retards)
- Meilleur carrier : **DHL Express** (25.3% retards)
- Pire carrier : **Budget Air Freight** (42.6% retards)

---

## 👤 AUTEUR

**Dorian**  
Master AI/Data Product Management  
Alternant CEVA Logistics  
📧 [email]  
🔗 [LinkedIn]

---

## 📄 LICENCE

Ce projet est développé dans le cadre d'un mémoire de Master.  
Données anonymisées et semi-fictives pour raisons de confidentialité.

---

## 🙏 REMERCIEMENTS

- **CEVA Logistics** pour l'accès aux données et le contexte business
- **Tuteur académique** pour l'encadrement scientifique
- **Équipes opérationnelles CEVA** pour les insights métier

---

**Dernière mise à jour :** Mars 2025  
**Version :** 1.0
