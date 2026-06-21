"""
SCRIPT 1 : GÉNÉRATION DATASET BRUT CEVA
========================================
Génère 40,800 lignes de données semi-fictives avec imperfections maîtrisées
Période : Janvier 2024 → Janvier 2026 (25 mois)
Modes : AIR (85%), ROAD (10%), SEA (5%)

Output : raw_shipments_full.csv
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

# Configuration
np.random.seed(42)
random.seed(42)

print("🚀 Génération du dataset BRUT CEVA...")
print("=" * 80)

# ============================================================================
# 1. PARAMÈTRES GLOBAUX
# ============================================================================

TOTAL_SHIPMENTS = 40000
DUPLICATE_RATE = 0.02  # 2% doublons
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 1, 31)

# Business Units
BU_DISTRIBUTION = {'AC': 0.613, 'ADS': 0.387}

# Modes de transport
MODE_DISTRIBUTION = {'AIR': 0.85, 'ROAD': 0.10, 'SEA': 0.05}

# Service types
SERVICE_DISTRIBUTION = {'RTN': 0.738, 'NRTN': 0.262}

# ============================================================================
# 2. AGENCES PAR PAYS (Codes IATA)
# ============================================================================

AGENCIES = {
    'FR': ['CDG', 'MRS', 'TLS'],
    'ES': ['MAD', 'SVQ'],
    'GB': ['LHR'],
    'DE': ['HAM', 'MUC'],
    'US': ['ATL', 'JFK', 'DFW', 'LAX', 'ORD', 'MIA'],
    'CA': ['YVR', 'YYC', 'YYZ'],
    'SG': ['SIN'],
    'CN': ['PEK', 'PVG', 'XIY', 'CAN', 'TSN'],
    'TK': ['IST', 'ADB', 'ESB'],
    # Pays tiers
    'AE': ['DXB', 'JED'],
    'SA': ['RUH'],
    'QA': ['DOH'],
    'MA': ['CMN'],
    'EG': ['CAI'],
    'ZA': ['JNB'],
    'IN': ['DEL'],
    'KR': ['ICN'],
    'JP': ['NRT'],
    'BR': ['GRU'],
    'PL': ['WAW']
}

# ============================================================================
# 3. ROUTES PRINCIPALES (avec volumes %)
# ============================================================================

MAIN_ROUTES = [
    ('US', 'FR', 0.230),  # 23.0%
    ('CN', 'ES', 0.130),  # 13.0%
    ('DE', 'ES', 0.105),  # 10.5%
    ('US', 'ES', 0.090),  # 9.0%
    ('FR', 'ES', 0.080),  # 8.0%
    ('CN', 'FR', 0.070),  # 7.0%
    ('US', 'DE', 0.060),  # 6.0%
    ('FR', 'DE', 0.050),  # 5.0%
    ('GB', 'ES', 0.040),  # 4.0%
    ('SG', 'ES', 0.030),  # 3.0%
]

# Routes secondaires (18.4%)
SECONDARY_ROUTES = [
    ('DE', 'FR', 0.035),
    ('GB', 'DE', 0.025),
    ('FR', 'GB', 0.020),
    ('CA', 'FR', 0.018),
    ('CA', 'ES', 0.016),
    ('US', 'GB', 0.014),
    ('CN', 'DE', 0.012),
    ('SG', 'FR', 0.010),
    ('TK', 'ES', 0.008),
    ('DE', 'GB', 0.007),
    ('ES', 'DE', 0.006),
    ('FR', 'US', 0.005),
    ('TK', 'DE', 0.004),
    ('GB', 'FR', 0.003),
]

# Routes pays tiers (6.4%)
TIER3_ROUTES = [
    ('ES', 'AE', 0.009),  # Défense
    ('ES', 'SA', 0.007),
    ('ES', 'QA', 0.006),
    ('ES', 'MA', 0.006),
    ('ES', 'EG', 0.004),
    ('FR', 'AE', 0.003),
    ('DE', 'IN', 0.003),
    ('FR', 'IN', 0.003),
    ('FR', 'MA', 0.002),
    ('DE', 'KR', 0.002),
    ('ES', 'BR', 0.003),
    ('FR', 'BR', 0.002),
    ('DE', 'PL', 0.002),
    ('ES', 'ZA', 0.002),
    ('FR', 'JP', 0.002),
    ('DE', 'JP', 0.001),
    ('GB', 'AE', 0.001),
]

ALL_ROUTES = MAIN_ROUTES + SECONDARY_ROUTES + TIER3_ROUTES

# ============================================================================
# 4. CARRIERS PAR MODE
# ============================================================================

CARRIERS_AIR = {
    # Excellents (34.2%)
    'DHL Express': {'perf': 0.877, 'weight': 0.148},
    'FedEx Express': {'perf': 0.849, 'weight': 0.116},
    'Singapore Airlines Cargo': {'perf': 0.821, 'weight': 0.078},
    
    # Moyens (46.3%)
    'Air France Cargo': {'perf': 0.722, 'weight': 0.122},
    'Lufthansa Cargo': {'perf': 0.754, 'weight': 0.097},
    'British Airways Cargo': {'perf': 0.698, 'weight': 0.081},
    'UPS': {'perf': 0.776, 'weight': 0.079},
    'Emirates SkyCargo': {'perf': 0.739, 'weight': 0.068},
    'Cathay Pacific Cargo': {'perf': 0.711, 'weight': 0.016},
    
    # Problématiques (19.5%)
    'DB Schenker Air': {'perf': 0.524, 'weight': 0.079},
    'Kuehne+Nagel Air': {'perf': 0.552, 'weight': 0.068},
    'Panalpina Air': {'perf': 0.483, 'weight': 0.048},
}

CARRIERS_ROAD = {
    'Geodis Road': {'perf': 0.92, 'weight': 0.35},
    'XPO Logistics': {'perf': 0.88, 'weight': 0.28},
    'Dachser': {'perf': 0.85, 'weight': 0.22},
    'Kuehne+Nagel Road': {'perf': 0.81, 'weight': 0.15},
}

CARRIERS_SEA = {
    'Maersk': {'perf': 0.68, 'weight': 0.45},
    'CMA CGM': {'perf': 0.71, 'weight': 0.35},
    'MSC': {'perf': 0.65, 'weight': 0.20},
}

# ============================================================================
# 5. EXCEPTION CODES
# ============================================================================

EXCEPTION_CODES = {
    'D04': 0.246,  # Goods Not Ready
    'D33': 0.198,  # Late Booking
    'D29': 0.179,  # Customs Delay
    'D20': 0.117,  # Waiting Instructions
    'D14': 0.083,  # Weather
    'D07': 0.071,  # Aircraft Delay
    'D41': 0.049,  # Documentation Issues
    'D52': 0.032,  # Capacity Issues
    'D18': 0.025,  # Carrier Delay
}

# ============================================================================
# 6. FONCTIONS UTILITAIRES
# ============================================================================

def generate_shipment_id():
    """Génère ID unique format SHP######"""
    return f"SHP{random.randint(100000, 999999)}"

def generate_cargowise_ref():
    """Génère référence CargoWise format S#######"""
    return f"S{random.randint(1000000, 9999999)}"

def generate_file_number(country, agency):
    """Génère numéro de dossier format PAYS-AGENCE-######"""
    return f"{country}-{agency}-{random.randint(100000, 999999)}"

def generate_customer_ref():
    """Génère référence Airbus"""
    prefix = random.choice(['AIR', 'ABS', 'FIN', 'STR'])
    return f"{prefix}{random.randint(10000, 99999)}"

def random_date_in_period(start, end):
    """Génère date aléatoire dans période avec saisonnalité et tendance"""
    # Saisonnalité mensuelle (multiplicateurs)
    seasonal_factors = {
        1: 1.15,   # Janvier: +15% (reprise post-vacances)
        2: 0.95,   # Février: -5%
        3: 1.05,   # Mars: +5%
        4: 1.00,   # Avril: normal
        5: 1.05,   # Mai: +5%
        6: 1.00,   # Juin: normal
        7: 0.85,   # Juillet: -15% (vacances)
        8: 0.75,   # Août: -25% (creux été)
        9: 1.10,   # Septembre: +10% (reprise)
        10: 1.05,  # Octobre: +5%
        11: 1.15,  # Novembre: +15% (préparation fêtes)
        12: 1.30   # Décembre: +30% (rush Noël)
    }
    
    # Probabilités pondérées par mois avec tendance de croissance
    delta = end - start
    total_months = 25  # Jan 2024 → Fév 2026
    
    # Créer distribution avec saisonnalité + tendance croissance (+12%/an = +1%/mois)
    month_probs = []
    current_date = start
    month_idx = 0
    
    while current_date < end:
        month = current_date.month
        year_offset = (current_date.year - 2024) * 12 + (month - 1)
        
        # Tendance croissance: +1% par mois
        growth_factor = 1 + (year_offset * 0.01)
        
        # Saisonnalité
        seasonal_factor = seasonal_factors[month]
        
        # Combiné
        combined_factor = growth_factor * seasonal_factor
        month_probs.append(combined_factor)
        
        # Mois suivant
        if month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, month + 1, 1)
        month_idx += 1
    
    # Normaliser probas
    total_prob = sum(month_probs)
    month_probs = [p / total_prob for p in month_probs]
    
    # Sélectionner mois selon distribution
    selected_month_idx = random.choices(range(len(month_probs)), weights=month_probs, k=1)[0]
    
    # Date de début du mois sélectionné
    months_from_start = selected_month_idx
    year_offset = months_from_start // 12
    month_offset = months_from_start % 12
    
    selected_year = start.year + year_offset
    selected_month = start.month + month_offset
    if selected_month > 12:
        selected_year += 1
        selected_month -= 12
    
    # Date aléatoire dans le mois sélectionné
    month_start = datetime(selected_year, selected_month, 1)
    if selected_month == 12:
        month_end = datetime(selected_year + 1, 1, 1) - timedelta(days=1)
    else:
        month_end = datetime(selected_year, selected_month + 1, 1) - timedelta(days=1)
    
    # Limiter à la période
    month_end = min(month_end, end)
    
    # Jour aléatoire dans le mois
    days_in_month = (month_end - month_start).days
    random_day = random.randint(0, days_in_month)
    
    return month_start + timedelta(days=random_day)

def working_days_between(start, end):
    """Calcule nombre de jours ouvrés entre 2 dates"""
    days = 0
    current = start
    while current <= end:
        if current.weekday() < 5:  # Lundi=0, Vendredi=4
            days += 1
        current += timedelta(days=1)
    return days

def select_weighted_random(options_dict):
    """Sélection aléatoire pondérée"""
    items = list(options_dict.keys())
    weights = [options_dict[k] if isinstance(options_dict[k], float) 
               else options_dict[k]['weight'] for k in items]
    return random.choices(items, weights=weights, k=1)[0]

# ============================================================================
# 7. GÉNÉRATION DES SHIPMENTS
# ============================================================================

print(f"\n📦 Génération de {TOTAL_SHIPMENTS} shipments...")

shipments = []

for i in range(TOTAL_SHIPMENTS):
    if (i + 1) % 5000 == 0:
        print(f"   Progress: {i+1}/{TOTAL_SHIPMENTS} ({(i+1)/TOTAL_SHIPMENTS*100:.1f}%)")
    
    # Business Unit
    bu = select_weighted_random(BU_DISTRIBUTION)
    
    # Mode de transport
    mode = select_weighted_random(MODE_DISTRIBUTION)
    
    # Service Type
    service_type = select_weighted_random(SERVICE_DISTRIBUTION)
    
    # Route (origine → destination)
    route = random.choices(
        [r[:2] for r in ALL_ROUTES],
        weights=[r[2] for r in ALL_ROUTES],
        k=1
    )[0]
    origin_country, dest_country = route
    
    # Agences origine et destination
    origin_agency = random.choice(AGENCIES[origin_country])
    dest_agency = random.choice(AGENCIES[dest_country])
    
    # Carrier selon mode
    if mode == 'AIR':
        carrier = select_weighted_random(CARRIERS_AIR)
        carrier_perf = CARRIERS_AIR[carrier]['perf']
    elif mode == 'ROAD':
        carrier = select_weighted_random(CARRIERS_ROAD)
        carrier_perf = CARRIERS_ROAD[carrier]['perf']
    else:  # SEA
        carrier = select_weighted_random(CARRIERS_SEA)
        carrier_perf = CARRIERS_SEA[carrier]['perf']
    
    # Dates
    creation_date = random_date_in_period(START_DATE, END_DATE)
    
    # Lead time selon mode et service
    if mode == 'AIR':
        if service_type == 'RTN':
            # Distance-based lead time
            if origin_country in ['FR', 'DE', 'ES', 'GB'] and dest_country in ['FR', 'DE', 'ES', 'GB']:
                base_lead_time = random.randint(2, 3)  # Intra-EU
            elif any(c in ['US', 'CA'] for c in [origin_country, dest_country]):
                base_lead_time = random.randint(5, 7)  # Transatlantic
            elif any(c in ['CN', 'SG', 'IN', 'JP', 'KR'] for c in [origin_country, dest_country]):
                base_lead_time = random.randint(7, 10)  # Asia
            else:
                base_lead_time = random.randint(6, 8)  # Autres
        else:  # NRTN
            base_lead_time = max(1, int(base_lead_time * 0.6))  # Express
    elif mode == 'ROAD':
        base_lead_time = 1  # ROAD toujours 1 jour
    else:  # SEA
        base_lead_time = random.randint(25, 35)  # Mer très long
    
    requested_pickup = creation_date + timedelta(days=random.randint(1, 3))
    requested_delivery = requested_pickup + timedelta(days=base_lead_time)
    
    # Hazardous (ADS plus probable)
    hazard_prob = 0.52 if bu == 'ADS' else 0.08
    is_hazardous = 'Y' if random.random() < hazard_prob else 'N'
    
    # Poids (log-normal distribution)
    if bu == 'ADS':
        weight_mean, weight_std = 3800, 1200
    else:
        weight_mean, weight_std = 1100, 450
    weight = max(10, np.random.lognormal(np.log(weight_mean), 0.6))
    
    # Volume
    volume = weight * random.uniform(0.0003, 0.0008)  # Ratio poids/volume
    
    # Nombre de pièces
    if weight < 500:
        pieces = random.randint(1, 3)
    elif weight < 2000:
        pieces = random.randint(2, 8)
    else:
        pieces = random.randint(5, 25)
    
    # Incoterm
    incoterms = ['DDP', 'DAP', 'EXW', 'FCA']
    incoterm = random.choice(incoterms)
    
    # Calcul retard (basé sur multiples facteurs)
    delay_prob = 1.0 - carrier_perf  # Base carrier
    
    # Ajustements MINIMAUX (objectif: Global ~22%)
    if is_hazardous == 'Y':
        delay_prob *= 1.08  # Hazardous = +8%
    if bu == 'ADS':
        delay_prob *= 1.05  # ADS = +5%
    if service_type == 'NRTN':
        delay_prob *= 0.75  # Express = -25%
    if dest_country in ['AE', 'SA', 'QA', 'MA', 'EG', 'ZA', 'IN', 'KR', 'JP', 'BR', 'PL']:
        delay_prob *= 1.05  # Tier3 = +5%
    if weight > 5000:
        delay_prob *= 1.03  # Heavy = +3%
    
    # Saisonnalité LISSÉE (variation max ±10%)
    month = creation_date.month
    season_factors = {
        1: 1.05, 2: 0.95, 3: 1.08, 4: 0.98, 5: 1.02, 6: 0.99,
        7: 1.03, 8: 1.06, 9: 0.97, 10: 1.01, 11: 1.04, 12: 1.10
    }
    delay_prob *= season_factors.get(month, 1.0)
    
    # BRUIT ALÉATOIRE INDIVIDUEL ±15%
    random_noise_delay = random.uniform(0.85, 1.15)
    delay_prob *= random_noise_delay
    
    # Cap probability (restrictif)
    delay_prob = min(0.65, max(0.03, delay_prob))
    
    is_delayed = random.random() < delay_prob
    
    # Dates réelles
    if is_delayed:
        delay_days = max(1, int(np.random.exponential(2.5)))
        actual_delivery = requested_delivery + timedelta(days=delay_days)
    else:
        # Parfois en avance
        if random.random() < 0.15:
            actual_delivery = requested_delivery - timedelta(days=random.randint(1, 2))
        else:
            actual_delivery = requested_delivery
    
    actual_pickup = requested_pickup + timedelta(days=random.randint(-1, 2))
    
    # Exception codes (si retard)
    exception_codes = None
    exception_count = 0
    if is_delayed:
        # Premier code
        exc1 = select_weighted_random(EXCEPTION_CODES)
        exception_codes = exc1
        exception_count = 1
        
        # Deuxième code (14.7% des retards)
        if random.random() < 0.147:
            exc2 = select_weighted_random(EXCEPTION_CODES)
            if exc2 != exc1:
                exception_codes += f"|{exc2}"
                exception_count = 2
                
                # Troisième code (2.3% des retards)
                if random.random() < 0.023:
                    exc3 = select_weighted_random(EXCEPTION_CODES)
                    if exc3 not in [exc1, exc2]:
                        exception_codes += f"|{exc3}"
                        exception_count = 3
    
    # Lead times
    if mode == 'AIR' and service_type == 'RTN':
        requested_lead_time = working_days_between(requested_pickup, requested_delivery)
        actual_lead_time = working_days_between(actual_pickup, actual_delivery)
    else:
        requested_lead_time = (requested_delivery - requested_pickup).days
        actual_lead_time = (actual_delivery - actual_pickup).days
    
    delay_value = (actual_delivery - requested_delivery).days
    
    # Original ETA (première estimation)
    original_eta = requested_delivery + timedelta(days=random.randint(-1, 1))
    
    # File numbers (selon pays avec agences)
    import_file = None
    export_file = None
    if origin_country in ['FR', 'DE', 'ES', 'GB', 'US', 'CA', 'SG', 'CN', 'TK']:
        export_file = generate_file_number(origin_country, origin_agency)
    if dest_country in ['FR', 'DE', 'ES', 'GB', 'US', 'CA', 'SG', 'CN', 'TK']:
        import_file = generate_file_number(dest_country, dest_agency)
    
    # Construction du shipment
    shipment = {
        'Shipment_ID': generate_shipment_id(),
        'CargoWise_Reference': generate_cargowise_ref(),
        'Import_File_Number': import_file,
        'Export_File_Number': export_file,
        'Customer_Reference': generate_customer_ref(),
        'Business_Unit': bu,
        'Creation_Date': creation_date.strftime('%Y-%m-%d'),
        'Requested_Pickup_Date': requested_pickup.strftime('%Y-%m-%d'),
        'Requested_Delivery_Date': requested_delivery.strftime('%Y-%m-%d'),
        'Actual_Pickup_Date': actual_pickup.strftime('%Y-%m-%d'),
        'Actual_Delivery_Date': actual_delivery.strftime('%Y-%m-%d'),
        'Original_ETA': original_eta.strftime('%Y-%m-%d'),
        'Origin_Country': origin_country,
        'Origin_City': origin_agency,
        'Destination_Country': dest_country,
        'Destination_City': dest_agency,
        'Carrier_Name': carrier,
        'Mode_of_Transport': mode,
        'Service_Type': service_type,
        'Gross_Weight_KG': round(weight, 2),
        'Gross_Volume_M3': round(volume, 4),
        'Number_of_Pieces': pieces,
        'Hazardous': is_hazardous,
        'Incoterm': incoterm,
        'Requested_Lead_Time_Days': requested_lead_time,
        'Actual_Lead_Time_Days': actual_lead_time,
        'Delay_Days': delay_value,
        'Is_Delayed': 1 if is_delayed else 0,
        'Exception_Codes': exception_codes,
        'Exception_Count': exception_count,
    }
    
    shipments.append(shipment)

# Créer DataFrame
df = pd.DataFrame(shipments)

print(f"\n✅ {len(df)} shipments générés")

# ============================================================================
# 8. INJECTION D'IMPERFECTIONS
# ============================================================================

print("\n🗑️ Injection d'imperfections contrôlées...")

# 8.1 Doublons (2%)
n_duplicates = int(TOTAL_SHIPMENTS * DUPLICATE_RATE)
duplicate_indices = np.random.choice(df.index, size=n_duplicates, replace=False)
duplicates = df.loc[duplicate_indices].copy()
df = pd.concat([df, duplicates], ignore_index=True)
print(f"   ✅ +{n_duplicates} doublons ajoutés ({len(df)} lignes total)")

# 8.2 Valeurs manquantes contrôlées
missing_configs = {
    'Exception_Codes': 0.05,  # 5% missing (normal si pas de retard)
    'Import_File_Number': 0.12,  # 12% (pays sans agence)
    'Export_File_Number': 0.12,
    'Original_ETA': 0.08,
}

for col, rate in missing_configs.items():
    if col in df.columns:
        n_missing = int(len(df) * rate)
        missing_idx = np.random.choice(df.index, size=n_missing, replace=False)
        df.loc[missing_idx, col] = np.nan

# Missing sur dates - gestion séparée pour cohérence
# Actual_Delivery_Date : 3% (shipments en cours/bloqués)
n_missing_delivery = int(len(df) * 0.03)
missing_delivery_idx = np.random.choice(df.index, size=n_missing_delivery, replace=False)
df.loc[missing_delivery_idx, 'Actual_Delivery_Date'] = np.nan

# Actual_Pickup_Date : 1% (pickup pas encore fait)
# Dont ~50% qui ont AUSSI Delivery manquant (shipment pas démarré)
n_missing_pickup = int(len(df) * 0.01)
n_both_missing = min(int(n_missing_pickup * 0.5), len(missing_delivery_idx))
both_missing_idx = np.random.choice(missing_delivery_idx, size=n_both_missing, replace=False)
remaining_pickup = n_missing_pickup - n_both_missing
available_idx = df.index.difference(missing_delivery_idx)
new_pickup_missing_idx = np.random.choice(available_idx, size=remaining_pickup, replace=False)
all_pickup_missing_idx = np.concatenate([both_missing_idx, new_pickup_missing_idx])
df.loc[all_pickup_missing_idx, 'Actual_Pickup_Date'] = np.nan

print(f"   ✅ Valeurs manquantes injectées")
print(f"      Actual_Delivery_Date: {n_missing_delivery}")
print(f"      Actual_Pickup_Date: {n_missing_pickup} (dont {n_both_missing} avec delivery aussi manquant)")

# CORRECTION INCOHÉRENCES : Si dates manquantes, nettoyer les métriques calculées
missing_dates_mask = df['Actual_Pickup_Date'].isna() | df['Actual_Delivery_Date'].isna()
n_to_fix = missing_dates_mask.sum()
df.loc[missing_dates_mask, 'Actual_Lead_Time_Days'] = np.nan
df.loc[missing_dates_mask, 'Delay_Days'] = np.nan
df.loc[missing_dates_mask, 'Is_Delayed'] = np.nan
# Exception_Codes et Exception_Count peuvent rester (cause du blocage)

print(f"   ✅ {n_to_fix} lignes corrigées (métriques mises à NaN si dates manquantes)")

# 8.3 Incohérences temporelles (5%)
n_inconsistent = int(len(df) * 0.05)
inconsistent_idx = np.random.choice(df.index, size=n_inconsistent, replace=False)

for idx in inconsistent_idx:
    error_type = random.choice(['pickup_after_delivery', 'creation_after_pickup', 'negative_leadtime'])
    
    if error_type == 'pickup_after_delivery':
        # Actual Pickup > Actual Delivery (erreur saisie)
        delivery_date = pd.to_datetime(df.at[idx, 'Actual_Delivery_Date'])
        if pd.notna(delivery_date):
            df.at[idx, 'Actual_Pickup_Date'] = (
                delivery_date + timedelta(days=random.randint(1, 3))
            ).strftime('%Y-%m-%d')
    
    elif error_type == 'creation_after_pickup':
        # Creation > Requested Pickup (bug système)
        pickup_date = pd.to_datetime(df.at[idx, 'Requested_Pickup_Date'])
        if pd.notna(pickup_date):
            df.at[idx, 'Creation_Date'] = (
                pickup_date + timedelta(days=random.randint(1, 2))
            ).strftime('%Y-%m-%d')

print(f"   ✅ {n_inconsistent} incohérences temporelles injectées")

# 8.4 Outliers extrêmes (0.5%)
n_outliers = int(len(df) * 0.005)
outlier_idx = np.random.choice(df.index, size=n_outliers, replace=False)
df.loc[outlier_idx, 'Gross_Weight_KG'] *= random.uniform(5, 10)  # Poids aberrant

print(f"   ✅ {n_outliers} outliers poids injectés")

# 8.5 Formats hétérogènes Exception_Codes
def messup_exception_format(code):
    if pd.isna(code) or random.random() > 0.15:
        return code
    
    variations = [
        code.lower(),  # d04 au lieu de D04
        code.replace('|', ','),  # Séparateur différent
        code + ' - Error',  # Format texte
        code.replace('D', 'DEL'),  # DEL04 au lieu de D04
    ]
    return random.choice(variations)

df['Exception_Codes'] = df['Exception_Codes'].apply(messup_exception_format)

print(f"   ✅ Formats exception codes variés")

# 8.6 Colonnes inutiles (à virer dans le nettoyage)
df['Internal_Reference_Legacy'] = [f"LEG{random.randint(1000, 9999)}" for _ in range(len(df))]
df['Operator_Name'] = [random.choice(['Jean', 'Marie', 'Pierre', 'Sophie', 'System']) for _ in range(len(df))]
df['System_Timestamp'] = [datetime.now().strftime('%Y-%m-%d %H:%M:%S') for _ in range(len(df))]
df['Comments'] = [''] * len(df)  # Vide

print(f"   ✅ Colonnes inutiles ajoutées")

# ============================================================================
# 9. EXPORT
# ============================================================================

import os

# Chemin absolu sécurisé
output_path = os.path.join(os.getcwd(), 'data', 'raw', 'raw_shipments_full.csv')
df.to_csv(output_path, index=False)

print("\n" + "=" * 80)
print(f"✅ DATASET BRUT GÉNÉRÉ : {output_path}")
print(f"📊 Lignes totales : {len(df):,}")
print(f"📊 Colonnes : {len(df.columns)}")
print("\n📋 STATISTIQUES:")
print(f"   - Modes : AIR {(df['Mode_of_Transport']=='AIR').sum():,}, ROAD {(df['Mode_of_Transport']=='ROAD').sum():,}, SEA {(df['Mode_of_Transport']=='SEA').sum():,}")
print(f"   - BU : AC {(df['Business_Unit']=='AC').sum():,}, ADS {(df['Business_Unit']=='ADS').sum():,}")
print(f"   - Retards : {df['Is_Delayed'].sum():,} ({df['Is_Delayed'].mean()*100:.1f}%)")
print(f"   - Doublons estimés : ~{n_duplicates}")
print(f"   - Incohérences : ~{n_inconsistent}")
print("=" * 80)
