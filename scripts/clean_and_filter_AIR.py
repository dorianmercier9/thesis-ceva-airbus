"""
SCRIPT 2 : NETTOYAGE & FILTRAGE DATASET
========================================
Nettoie le dataset brut et filtre uniquement le mode AIR
Input : raw_shipments_full.csv (~40,800 lignes)
Output : shipments_clean_AIR.csv (~32-34,000 lignes AIR)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

print("🧹 Nettoyage et filtrage du dataset CEVA...")
print("=" * 80)

# ============================================================================
# 1. CHARGEMENT
# ============================================================================

print("\n📂 Chargement du dataset brut...")
input_path = os.path.join(os.getcwd(), 'data', 'raw', 'raw_shipments_full.csv')
df = pd.read_csv(input_path)

print(f"✅ Dataset chargé : {len(df):,} lignes, {len(df.columns)} colonnes")
print(f"\n📊 État initial:")
print(f"   - Modes : AIR {(df['Mode_of_Transport']=='AIR').sum():,}, ROAD {(df['Mode_of_Transport']=='ROAD').sum():,}, SEA {(df['Mode_of_Transport']=='SEA').sum():,}")

# ============================================================================
# 2. DÉDOUBLONNAGE
# ============================================================================

print("\n🗑️ Étape 1 : Dédoublonnage...")
initial_count = len(df)

# Dédoublonner sur Shipment_ID
df = df.drop_duplicates(subset=['Shipment_ID'], keep='first')

duplicates_removed = initial_count - len(df)
print(f"   ✅ {duplicates_removed} doublons supprimés")
print(f"   📊 Lignes restantes : {len(df):,}")

# ============================================================================
# 3. SUPPRESSION COLONNES INUTILES
# ============================================================================

print("\n🗑️ Étape 2 : Suppression colonnes inutiles...")

useless_cols = ['Internal_Reference_Legacy', 'Operator_Name', 'System_Timestamp', 'Comments']
existing_useless = [col for col in useless_cols if col in df.columns]
df = df.drop(columns=existing_useless)

print(f"   ✅ {len(existing_useless)} colonnes supprimées : {', '.join(existing_useless) if existing_useless else 'aucune'}")
print(f"   📊 Colonnes restantes : {len(df.columns)}")

# ============================================================================
# 4. CONVERSION TYPES
# ============================================================================

print("\n🔄 Étape 3 : Conversion des types...")

# Dates
date_cols = ['Creation_Date', 'Requested_Pickup_Date', 'Requested_Delivery_Date',
             'Actual_Pickup_Date', 'Actual_Delivery_Date', 'Original_ETA']

for col in date_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

print(f"   ✅ {len(date_cols)} colonnes dates converties")

# Numériques
numeric_cols = ['Gross_Weight_KG', 'Gross_Volume_M3', 'Number_of_Pieces',
                'Requested_Lead_Time_Days', 'Actual_Lead_Time_Days', 'Delay_Days',
                'Is_Delayed', 'Exception_Count']

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"   ✅ {len(numeric_cols)} colonnes numériques converties")

# ============================================================================
# 5. STANDARDISATION EXCEPTION CODES
# ============================================================================

print("\n🔧 Étape 4 : Standardisation Exception_Codes...")

def standardize_exception_codes(code):
    """Nettoie et standardise les codes exception"""
    if pd.isna(code) or code == '':
        return None
    
    code = str(code).upper()  # Tout en majuscules
    code = code.replace(',', '|')  # Séparateur uniforme
    code = code.replace(' - ERROR', '')  # Virer texte
    code = code.replace(' - ', '')
    code = code.replace('DEL', 'D')  # DEL04 → D04
    
    # Split et clean chaque code
    codes = [c.strip() for c in code.split('|') if c.strip()]
    
    # Garder seulement codes valides (D## format)
    valid_codes = [c for c in codes if c.startswith('D') and len(c) >= 3]
    
    if not valid_codes:
        return None
    
    # Déduplicate
    unique_codes = list(dict.fromkeys(valid_codes))
    
    return '|'.join(unique_codes)

df['Exception_Codes'] = df['Exception_Codes'].apply(standardize_exception_codes)

# Recalculer Exception_Count
df['Exception_Count'] = df['Exception_Codes'].apply(
    lambda x: len(x.split('|')) if pd.notna(x) else 0
)

print(f"   ✅ Exception codes standardisés")
print(f"   📊 Codes valides : {df['Exception_Codes'].notna().sum():,}")

# ============================================================================
# 6. CORRECTION INCOHÉRENCES TEMPORELLES
# ============================================================================

print("\n🔧 Étape 5 : Correction incohérences temporelles...")

inconsistencies_fixed = 0

# 6.1 Actual_Pickup > Actual_Delivery (swap si les deux sont présents)
mask = (df['Actual_Pickup_Date'].notna()) & (df['Actual_Delivery_Date'].notna()) & (df['Actual_Pickup_Date'] > df['Actual_Delivery_Date'])
if mask.sum() > 0:
    df.loc[mask, ['Actual_Pickup_Date', 'Actual_Delivery_Date']] = df.loc[mask, ['Actual_Delivery_Date', 'Actual_Pickup_Date']].values
    inconsistencies_fixed += mask.sum()

# 6.2 Creation > Requested_Pickup (set Creation = Requested_Pickup - 1 day)
mask = df['Creation_Date'] > df['Requested_Pickup_Date']
if mask.sum() > 0:
    df.loc[mask, 'Creation_Date'] = df.loc[mask, 'Requested_Pickup_Date'] - timedelta(days=1)
    inconsistencies_fixed += mask.sum()

# 6.3 Requested_Pickup > Requested_Delivery (inverser)
mask = df['Requested_Pickup_Date'] > df['Requested_Delivery_Date']
if mask.sum() > 0:
    df.loc[mask, ['Requested_Pickup_Date', 'Requested_Delivery_Date']] = df.loc[mask, ['Requested_Delivery_Date', 'Requested_Pickup_Date']].values
    inconsistencies_fixed += mask.sum()

print(f"   ✅ {inconsistencies_fixed} incohérences corrigées")

# ============================================================================
# 7. FILTRAGE MODE AIR UNIQUEMENT
# ============================================================================

print("\n✂️ Étape 6 : Filtrage MODE AIR uniquement...")

initial_count = len(df)
df = df[df['Mode_of_Transport'] == 'AIR'].copy()
filtered_count = initial_count - len(df)

print(f"   ✅ {filtered_count} lignes non-AIR supprimées (ROAD + SEA)")
print(f"   📊 Lignes AIR restantes : {len(df):,}")

# ============================================================================
# 8. VÉRIFICATIONS QUALITÉ FINALES
# ============================================================================

print("\n🔍 Étape 7 : Vérifications qualité finales...")

# 8.1 Seule colonne vraiment critique : Creation_Date
critical_cols = ['Creation_Date']

missing_critical = df[critical_cols].isnull().sum()
if missing_critical.sum() > 0:
    print(f"   ⚠️ Valeurs manquantes sur colonne critique (Creation_Date) : {missing_critical.sum()}")
    df = df.dropna(subset=critical_cols)
    print(f"   ✅ Lignes avec Creation_Date manquant supprimées")

# 8.2 Valeurs infinies
inf_mask = np.isinf(df.select_dtypes(include=[np.number])).any(axis=1)
if inf_mask.sum() > 0:
    df = df[~inf_mask]
    print(f"   ✅ {inf_mask.sum()} lignes avec valeurs infinies supprimées")

# 8.3 Lead times négatifs (IGNORER les NaN - shipments en cours)
negative_lead_mask = (df['Actual_Lead_Time_Days'].notna()) & (df['Actual_Lead_Time_Days'] < 0)
if negative_lead_mask.sum() > 0:
    df = df[~negative_lead_mask]
    print(f"   ✅ {negative_lead_mask.sum()} lignes avec lead time négatif supprimées")

print(f"\n   📊 Dataset final : {len(df):,} lignes propres")

# ============================================================================
# 9. STATISTIQUES FINALES
# ============================================================================

print("\n📊 STATISTIQUES FINALES:")
print("=" * 80)

print(f"\n🔢 VOLUME:")
print(f"   - Total lignes : {len(df):,}")
print(f"   - Période : {df['Creation_Date'].min().date()} → {df['Creation_Date'].max().date()}")

# Statistiques dates manquantes
missing_pickup = df['Actual_Pickup_Date'].isna().sum()
missing_delivery = df['Actual_Delivery_Date'].isna().sum()
print(f"\n📅 DATES MANQUANTES (shipments en cours):")
print(f"   - Actual_Pickup_Date : {missing_pickup:,} ({missing_pickup/len(df)*100:.1f}%)")
print(f"   - Actual_Delivery_Date : {missing_delivery:,} ({missing_delivery/len(df)*100:.1f}%)")

print(f"\n🏢 BUSINESS UNITS:")
bu_counts = df['Business_Unit'].value_counts()
for bu, count in bu_counts.items():
    print(f"   - {bu}: {count:,} ({count/len(df)*100:.1f}%)")

print(f"\n✈️ SERVICE TYPE:")
service_counts = df['Service_Type'].value_counts()
for st, count in service_counts.items():
    print(f"   - {st}: {count:,} ({count/len(df)*100:.1f}%)")

print(f"\n⚠️ RETARDS (hors shipments en cours):")
completed_shipments = df['Is_Delayed'].notna()
delay_count = df[completed_shipments]['Is_Delayed'].sum()
completed_count = completed_shipments.sum()
print(f"   - Shipments terminés : {completed_count:,}")
print(f"   - Retards : {int(delay_count):,} ({delay_count/completed_count*100:.1f}%)")
print(f"   - À l'heure : {int(completed_count-delay_count):,} ({(completed_count-delay_count)/completed_count*100:.1f}%)")

print(f"\n🌍 TOP 5 ROUTES:")
df['Route'] = df['Origin_Country'] + '→' + df['Destination_Country']
top_routes = df['Route'].value_counts().head(5)
for route, count in top_routes.items():
    print(f"   - {route}: {count:,} ({count/len(df)*100:.1f}%)")

print(f"\n🚚 TOP 5 CARRIERS:")
top_carriers = df['Carrier_Name'].value_counts().head(5)
for carrier, count in top_carriers.items():
    carrier_completed = df[(df['Carrier_Name']==carrier) & df['Is_Delayed'].notna()]
    if len(carrier_completed) > 0:
        delay_rate = carrier_completed['Is_Delayed'].mean() * 100
        print(f"   - {carrier}: {count:,} ({count/len(df)*100:.1f}%) - {delay_rate:.1f}% retards")
    else:
        print(f"   - {carrier}: {count:,} ({count/len(df)*100:.1f}%) - N/A retards")

print(f"\n📦 CARACTÉRISTIQUES:")
print(f"   - Poids moyen : {df['Gross_Weight_KG'].mean():.0f} kg")
print(f"   - Volume moyen : {df['Gross_Volume_M3'].mean():.3f} m³")
print(f"   - Lead time moyen (terminés) : {df['Actual_Lead_Time_Days'].mean():.1f} jours")
print(f"   - Hazardous : {(df['Hazardous']=='Y').sum():,} ({(df['Hazardous']=='Y').mean()*100:.1f}%)")

print(f"\n🔧 QUALITÉ DONNÉES:")
missing_pct = (df.isnull().sum() / len(df) * 100).round(2)
missing_cols = missing_pct[missing_pct > 0].sort_values(ascending=False)
if len(missing_cols) > 0:
    print(f"   - Colonnes avec valeurs manquantes :")
    for col, pct in missing_cols.items():
        print(f"     • {col}: {pct:.1f}%")
else:
    print(f"   - ✅ Aucune valeur manquante")

# ============================================================================
# 10. EXPORT
# ============================================================================

output_path = os.path.join(os.getcwd(), 'data', 'processed', 'shipments_clean_AIR.csv')
df.to_csv(output_path, index=False)

print("\n" + "=" * 80)
print(f"✅ DATASET PROPRE GÉNÉRÉ : {output_path}")
print(f"📊 Lignes finales : {len(df):,}")
print(f"📊 Colonnes : {len(df.columns)}")
print(f"📊 Taux de complétude : {((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100):.1f}%")
print("=" * 80)

print("\n🎯 PRÊT POUR :")
print("   ✅ Module 1 : Demand Forecasting")
print("   ✅ Module 2 : Delay Prediction")
print("   ✅ Module 3 : Performance Intelligence")
