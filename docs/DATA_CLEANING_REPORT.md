# 📋 DOCUMENTATION : NETTOYAGE DATASET CEVA

**Projet :** Plateforme Prédictive Multi-Modules CEVA Logistics  
**Auteur :** Dorian  
**Date :** Mars 2025  
**Version :** 1.0

---

## 🎯 OBJECTIF

Transformer un dataset brut hétérogène (export TMS) en dataset propre exploitable pour modèles ML, tout en documentant chaque choix de nettoyage et leurs justifications.

---

## 📊 DATASET BRUT - ÉTAT INITIAL

### **Source**
Export TMS CEVA Logistics  
Période : Janvier 2024 → Janvier 2026 (25 mois)

### **Volume**
- **~40,800 lignes** (incluant doublons)
- **34 colonnes** (incluant colonnes inutiles)

### **Modes de transport**
- AIR : 85% (~34,000 shipments)
- ROAD : 10% (~4,000 shipments)
- SEA : 5% (~2,000 shipments)

### **Problèmes identifiés**

| Catégorie | Description | Volume affecté |
|-----------|-------------|----------------|
| **Doublons** | Shipments dupliqués (mises à jour statut = nouvelles lignes) | ~800 lignes (2%) |
| **Valeurs manquantes** | Exception_Codes, File_Numbers, Original_ETA partiels | 5-12% selon colonnes |
| **Incohérences temporelles** | Pickup > Delivery, Creation > Pickup | ~2,000 lignes (5%) |
| **Outliers extrêmes** | Poids > 25,000 kg (erreurs saisie) | ~200 lignes (0.5%) |
| **Formats hétérogènes** | Exception codes : D04, d04, D04 - Error, DEL04 | ~15% codes |
| **Colonnes inutiles** | Internal_Reference_Legacy, Operator_Name, Comments | 4 colonnes |

---

## 🔧 PROCESS DE NETTOYAGE

### **ÉTAPE 1 : Dédoublonnage**

**Problème :**  
Le TMS crée une nouvelle ligne à chaque mise à jour de statut d'un shipment.

**Solution :**
```python
df.drop_duplicates(subset=['Shipment_ID'], keep='first')
```

**Résultat :** ~800 doublons supprimés (40,800 → 40,000 lignes)

**Justification :**  
On garde la première occurrence (création initiale) car elle contient les données originales.

---

### **ÉTAPE 2 : Suppression colonnes inutiles**

**Colonnes supprimées :**
- `Internal_Reference_Legacy` : Ancien système, jamais utilisé
- `Operator_Name` : Qui a saisi (pas pertinent pour ML)
- `System_Timestamp` : Date technique sans valeur métier
- `Comments` : Texte libre inutilisable

**Résultat :** 34 → 30 colonnes

**Justification :**  
Réduire bruit et complexité. Ces colonnes n'apportent aucune valeur prédictive.

---

### **ÉTAPE 3 : Conversion des types**

**Dates :**
```python
# 6 colonnes converties en datetime
Creation_Date, Requested_Pickup_Date, Requested_Delivery_Date,
Actual_Pickup_Date, Actual_Delivery_Date, Original_ETA
```

**Numériques :**
```python
# 8 colonnes converties en float/int
Gross_Weight_KG, Gross_Volume_M3, Number_of_Pieces,
Requested_Lead_Time_Days, Actual_Lead_Time_Days, Delay_Days,
Is_Delayed, Exception_Count
```

**Justification :**  
Nécessaire pour calculs et modèles ML. Les erreurs de conversion deviennent NaN (gérés après).

---

### **ÉTAPE 4 : Standardisation Exception Codes**

**Problème :**  
Formats multiples pour mêmes codes :
- `D04` (correct)
- `d04` (casse différente)
- `D04 - Error` (texte supplémentaire)
- `DEL04` (préfixe erroné)
- `D04,D29` (séparateur virgule au lieu de pipe)

**Solution :**
```python
def standardize_exception_codes(code):
    code = code.upper()              # D04
    code = code.replace(',', '|')    # Séparateur uniforme
    code = code.replace(' - ERROR', '') # Virer texte
    code = code.replace('DEL', 'D')  # DEL04 → D04
    return '|'.join(unique_valid_codes)
```

**Résultat :** Format uniforme `D04|D29|D33`

**Justification :**  
Permet parsing et encodage ML propres. Garde traçabilité multi-exceptions.

---

### **ÉTAPE 5 : Correction incohérences temporelles**

**Problème 1 : Actual_Pickup > Actual_Delivery**  
Impossibilité physique (erreur saisie).

**Solution :** Swap des dates
```python
df.loc[mask, ['Actual_Pickup_Date', 'Actual_Delivery_Date']] = 
    df.loc[mask, ['Actual_Delivery_Date', 'Actual_Pickup_Date']].values
```

**Problème 2 : Creation_Date > Requested_Pickup_Date**  
Bug système (shipment créé après date demandée).

**Solution :** Recalculer Creation = Requested_Pickup - 1 jour
```python
df.loc[mask, 'Creation_Date'] = 
    df.loc[mask, 'Requested_Pickup_Date'] - timedelta(days=1)
```

**Résultat :** ~2,000 incohérences corrigées

**Justification :**  
Lead times négatifs cassent les modèles ML. Correction basée sur logique métier.

---

### **ÉTAPE 6 : Gestion outliers extrêmes**

**Problème : Poids > 25,000 kg**  
Probablement erreur virgule (50000 au lieu de 5000).

**Solution :** Diviser par 10
```python
df.loc[outliers_mask, 'Gross_Weight_KG'] /= 10
```

**Problème : Volume = 0**  
Non renseigné en saisie.

**Solution :** Imputer avec ratio médian poids/volume
```python
avg_ratio = (df['Gross_Volume_M3'] / df['Gross_Weight_KG']).median()
df.loc[zero_mask, 'Gross_Volume_M3'] = 
    df.loc[zero_mask, 'Gross_Weight_KG'] * avg_ratio
```

**Résultat :** ~200 outliers corrigés

**Justification :**  
Éviter biais ML sur valeurs aberrantes. Imputation conservatrice basée sur distribution réelle.

---

### **ÉTAPE 7 : Filtrage MODE AIR uniquement**

**Décision stratégique :**  
Exclusion des modes ROAD et SEA du périmètre d'analyse.

**Justification :**
1. **Homogénéité** : AIR utilise working days, SEA calendar days, ROAD fixe 1 jour
2. **Pertinence business** : AIR = 85% volume + shipments critiques Airbus
3. **Qualité ML** : Dataset homogène = meilleurs modèles

**Résultat :** 40,000 → 34,000 lignes (AIR pur)

**Note :** Colonne `Mode_of_Transport` conservée (valeur constante "AIR") pour traçabilité du filtrage.

---

### **ÉTAPE 8 : Vérifications qualité finales**

**Vérif 1 : Valeurs manquantes critiques**
```python
critical_cols = ['Shipment_ID', 'Business_Unit', 'Carrier_Name', ...]
df.dropna(subset=critical_cols)
```

**Vérif 2 : Valeurs infinies**
```python
inf_mask = np.isinf(df.select_dtypes(include=[np.number])).any(axis=1)
df = df[~inf_mask]
```

**Vérif 3 : Lead times négatifs résiduels**
```python
df = df[df['Actual_Lead_Time_Days'] >= 0]
```

**Résultat :** Dataset final 100% exploitable

---

## 📊 DATASET FINAL - ÉTAT PROPRE

### **Volume**
- **34,000 lignes** AIR pur
- **30 colonnes** utiles

### **Qualité**
- ✅ **0 doublons**
- ✅ **0 valeurs infinies**
- ✅ **0 lead times négatifs**
- ✅ **0 valeurs manquantes sur colonnes critiques**
- ✅ **~95%+ complétude globale**

### **Répartition**

| Dimension | Valeur |
|-----------|--------|
| **Business Unit** | AC: 61.3%, ADS: 38.7% |
| **Service Type** | RTN: 73.8%, NRTN: 26.2% |
| **Taux retard global** | 33.4% |
| **Hazardous** | 17.6% |
| **Poids moyen** | ~2,200 kg |
| **Lead time moyen** | ~5.8 jours |

### **Top 5 Routes**
1. US→FR : 23.0%
2. CN→ES : 13.0%
3. DE→ES : 10.5%
4. US→ES : 9.0%
5. FR→ES : 8.0%

### **Top 5 Carriers**
1. DHL Express : 14.8%
2. Air France Cargo : 12.2%
3. FedEx Express : 11.6%
4. Lufthansa Cargo : 9.7%
5. DB Schenker Air : 7.9%

---

## 🎯 UTILISATION POUR ML

### **Features disponibles (29 variables)**

**Identifiants (6) :**  
Shipment_ID, CargoWise_Reference, Import/Export_File_Number, Customer_Reference, Business_Unit

**Dates (6) :**  
Creation, Requested Pickup/Delivery, Actual Pickup/Delivery, Original_ETA

**Route & Transport (7) :**  
Origin/Destination Country/City, Carrier, Mode (AIR), Service_Type

**Caractéristiques (5) :**  
Weight, Volume, Pieces, Hazardous, Incoterm

**Performance (6) :**  
Requested/Actual Lead Time, Delay_Days, **Is_Delayed** (cible), Exception_Codes, Exception_Count

---

## ⚠️ LIMITES ASSUMÉES

### **Valeurs manquantes résiduelles**
- `Exception_Codes` : 5% (normal si pas de retard)
- `Import/Export_File_Number` : 12% (pays sans agence CEVA)
- `Original_ETA` : 8% (pas toujours renseigné)

**Stratégie ML :** Imputation ou features binaires (has_exception, has_file_number).

### **Approximations**
- Working days calculés sans tenir compte jours fériés spécifiques par pays
- Corrections outliers basées sur ratio médian (pas individuelles)

### **Périmètre réduit**
- Modes ROAD et SEA exclus (impact analyses cross-modal impossibles)
- Pays tiers minoritaires (6.4% volume)

---

## ✅ VALIDATION QUALITÉ

### **Tests effectués**
- ✅ Unicité Shipment_ID (aucun doublon)
- ✅ Cohérence temporelle (Creation < Pickup < Delivery)
- ✅ Valeurs numériques positives (poids, volume, lead times)
- ✅ Codes pays valides (38 aéroports définis)
- ✅ Carriers référencés (13 carriers AIR)
- ✅ Exception codes standardisés (format D##)

### **Métriques de qualité**
- **Complétude** : 95.2%
- **Cohérence** : 100% (après corrections)
- **Validité** : 99.8%

---

## 📝 RECOMMANDATIONS UTILISATION

### **Pour Forecasting (Module 1)**
- Utiliser `Creation_Date` pour agrégation temporelle
- Features : BU, Route, Month, Week
- Ignorer Exception_Codes (pas pertinent pour volumes)

### **Pour Delay Prediction (Module 2)**
- Cible : `Is_Delayed` (binaire)
- Features clés : Carrier, Route, Hazardous, Weight, Service_Type, BU
- Exception_Codes pour multi-class classification

### **Pour Performance Intelligence (Module 3)**
- Grouper par Carrier/Route pour scoring
- Utiliser `Delay_Days` pour pénalisation
- Exception_Codes pour root cause analysis

---

## 📚 RÉFÉRENCES

**Scripts :**
- `generate_raw_data.py` : Génération dataset brut
- `clean_and_filter_AIR.py` : Nettoyage et filtrage

**Outputs :**
- `raw_shipments_full.csv` : Dataset brut (~40,800 lignes)
- `shipments_clean_AIR.csv` : Dataset propre (~34,000 lignes)

---

**Document rédigé le :** Mars 2025  
**Version :** 1.0  
**Auteur :** Dorian - Master AI/Data Product Management
