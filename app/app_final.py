import streamlit as st
import pickle
import pandas as pd
import json
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(page_title="CEVA - Analyse Retards", layout="wide", initial_sidebar_state="expanded")

BASE_DIR           = Path(__file__).parent
MODEL_PATH         = BASE_DIR.parent / "models" / "random_forest_corrected.pkl"
SCALER_PATH        = BASE_DIR.parent / "models" / "scaler_corrected.pkl"
CARRIER_STATS_PATH = BASE_DIR / "data" / "carrier_full_stats.json"
ROUTE_STATS_PATH   = BASE_DIR / "data" / "route_full_stats.json"
BATCH_META_PATH    = BASE_DIR / "data" / "last_batch_meta.json"
DB_PATH            = BASE_DIR / "data" / "ceva_analytics.db"

DEFAULT_DELAY_RATE = 0.27
DEFAULT_VOLUME     = 500
TOP_K              = 50
WINDOW_DAYS        = 30

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    [data-testid="stSidebar"] { background-color: #001E50; }
    [data-testid="stSidebar"] * { color: white !important; }

    .page-header {
        border-left: 4px solid #E30613;
        padding: 0.6rem 1rem;
        background-color: #F5F7FA;
        margin-bottom: 1.5rem;
    }
    .page-header h2 { margin: 0; font-size: 1.3rem; color: #001E50; font-weight: 600; }
    .page-header p  { margin: 0.2rem 0 0 0; font-size: 0.85rem; color: #555; }

    .summary-bar {
        background-color: #F5F7FA;
        border: 1px solid #DDE2EA;
        padding: 0.8rem 1.2rem;
        border-radius: 3px;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
        color: #333;
    }

    .section-label {
        font-size: 0.85rem;
        font-weight: 700;
        letter-spacing: 1px;
        color: #FFFFFF;
        background-color: #001E50;
        text-transform: uppercase;
        margin: 1.5rem 0 0.5rem 0;
        padding: 0.5rem 1rem;
        border-radius: 3px;
    }

    .section-label-secondary {
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 1px;
        color: #555555;
        background-color: #F5F7FA;
        text-transform: uppercase;
        margin: 1.5rem 0 0.5rem 0;
        padding: 0.5rem 1rem;
        border-radius: 3px;
        border: 1px solid #DDE2EA;
    }

    .stButton > button { background-color: #E30613; color: white; border: none; font-weight: 600; }
    .stButton > button:hover { background-color: #B00510; color: white; }
    [data-testid="stMetricValue"] { color: #333333; font-weight: 700; }
    .stDataFrame { font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ENCODINGS
# ============================================================
ORIGIN_ENC   = {'CA':0,'CN':1,'DE':2,'ES':3,'FR':4,'GB':5,'SG':6,'TK':7,'US':8}
DEST_ENC     = {'AE':0,'BR':1,'DE':2,'EG':3,'ES':4,'FR':5,'GB':6,'IN':7,'JP':8,'KR':9,'MA':10,'PL':11,'QA':12,'SA':13,'US':14,'ZA':15}
CARRIER_ENC  = {'Air France Cargo':0,'British Airways Cargo':1,'Cathay Pacific Cargo':2,'DB Schenker Air':3,'DHL Express':4,'Emirates SkyCargo':5,'FedEx Express':6,'Kuehne+Nagel Air':7,'Lufthansa Cargo':8,'Panalpina Air':9,'Singapore Airlines Cargo':10,'UPS':11}
INCOTERM_ENC = {'DAP':0,'DDP':1,'EXW':2,'FCA':3}
ROUTE_ENC    = {'CA→ES':0,'CA→FR':1,'CN→DE':2,'CN→ES':3,'CN→FR':4,'DE→ES':5,'DE→FR':6,'DE→GB':7,'DE→IN':8,'DE→JP':9,'DE→KR':10,'DE→PL':11,'ES→AE':12,'ES→BR':13,'ES→DE':14,'ES→EG':15,'ES→MA':16,'ES→QA':17,'ES→SA':18,'ES→ZA':19,'FR→AE':20,'FR→BR':21,'FR→DE':22,'FR→ES':23,'FR→GB':24,'FR→IN':25,'FR→JP':26,'FR→MA':27,'FR→US':28,'GB→AE':29,'GB→DE':30,'GB→ES':31,'GB→FR':32,'SG→ES':33,'SG→FR':34,'TK→DE':35,'TK→ES':36,'US→DE':37,'US→ES':38,'US→FR':39,'US→GB':40}

FEATURE_ORDER = [
    'Origin_Country','Destination_Country','Route','Carrier_Name','Incoterm',
    'Gross_Weight_KG','Gross_Volume_M3','Number_of_Pieces','Requested_Lead_Time_Days',
    'Month','Year','Pickup_DayOfWeek','Delivery_DayOfWeek','Pickup_IsWeekend','Delivery_IsWeekend',
    'Business_Unit_ADS','Service_Type_RTN','Hazardous_Y',
    'Weight_Category_Light','Weight_Category_Medium','Weight_Category_VeryHeavy',
    'Carrier_Delay_Rate','Carrier_Volume','Route_Delay_Rate','Route_Volume',
    'Weight_Per_Piece','Is_Rush','Is_High_Piece_Count'
]

# ============================================================
# CHARGEMENT
# ============================================================
@st.cache_resource
def load_models():
    with open(MODEL_PATH,  'rb') as f: model  = pickle.load(f)
    with open(SCALER_PATH, 'rb') as f: scaler = pickle.load(f)
    return model, scaler

@st.cache_data
def load_stats():
    with open(CARRIER_STATS_PATH) as f: carrier_stats = json.load(f)
    with open(ROUTE_STATS_PATH)   as f: route_stats   = json.load(f)
    return carrier_stats, route_stats

try:
    model, scaler              = load_models()
    carrier_stats, route_stats = load_stats()
except Exception as e:
    st.error(f"Erreur chargement : {e}")
    st.stop()

# ============================================================
# BASE DE DONNEES SQLITE
# ============================================================
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(DB_PATH.parent, exist_ok=True)
    conn = get_db()
    conn.execute("CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY AUTOINCREMENT, date_analyse TEXT NOT NULL, periode_debut TEXT, periode_fin TEXT, total INTEGER, ignored INTEGER DEFAULT 0)")
    conn.execute("CREATE TABLE IF NOT EXISTS resultats (id INTEGER PRIMARY KEY AUTOINCREMENT, analyse_id INTEGER NOT NULL, shipment_id TEXT, customer_reference TEXT, route TEXT, carrier_name TEXT, business_unit TEXT, pickup_date TEXT, lead_time INTEGER, score_risque REAL, rang INTEGER, priorite TEXT, rang_relatif TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS suivis (shipment_id TEXT PRIMARY KEY, pickup_date TEXT NOT NULL, marked_at TEXT NOT NULL, active INTEGER DEFAULT 1)")
    conn.execute("CREATE TABLE IF NOT EXISTS unknown_elements (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT NOT NULL, valeur TEXT NOT NULL, shipment_id TEXT NOT NULL, detected_at TEXT NOT NULL, UNIQUE(type, valeur, shipment_id))")
    conn.commit()
    conn.close()

init_db()

def load_unknown_log():
    try:
        conn = get_db()
        cursor = conn.execute("SELECT valeur, GROUP_CONCAT(DISTINCT shipment_id) FROM unknown_elements WHERE type='carrier' GROUP BY valeur")
        carriers = {row[0]: row[1].split(',') if row[1] else [] for row in cursor.fetchall()}
        cursor = conn.execute("SELECT valeur, GROUP_CONCAT(DISTINCT shipment_id) FROM unknown_elements WHERE type='route' GROUP BY valeur")
        routes = {row[0]: row[1].split(',') if row[1] else [] for row in cursor.fetchall()}
        cursor = conn.execute("SELECT MAX(detected_at) FROM unknown_elements")
        last_update = cursor.fetchone()[0] or ""
        conn.close()
        return {"transporteurs_inconnus": carriers, "routes_inconnues": routes, "derniere_mise_a_jour": last_update}
    except Exception:
        return {"transporteurs_inconnus": {}, "routes_inconnues": {}, "derniere_mise_a_jour": ""}

def save_unknown_log(log):
    conn = get_db()
    conn.execute("DELETE FROM unknown_elements")
    conn.commit()
    conn.close()

def save_unknown_elements(unknown_carriers, unknown_routes):
    conn = get_db()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    for carrier, shipment_ids in unknown_carriers.items():
        for sid in shipment_ids:
            try:
                conn.execute("INSERT OR IGNORE INTO unknown_elements (type, valeur, shipment_id, detected_at) VALUES (?, ?, ?, ?)", ('carrier', carrier, sid, now))
            except Exception:
                pass
    for route, shipment_ids in unknown_routes.items():
        for sid in shipment_ids:
            try:
                conn.execute("INSERT OR IGNORE INTO unknown_elements (type, valeur, shipment_id, detected_at) VALUES (?, ?, ?, ?)", ('route', route, sid, now))
            except Exception:
                pass
    conn.commit()
    conn.close()

def load_treated():
    try:
        conn = get_db()
        # Charger tous les suivis actifs et filtrer en Python avec de vrais datetime
        cursor = conn.execute("SELECT shipment_id, pickup_date, marked_at FROM suivis WHERE active=1")
        today = datetime.now().date()
        result = {}
        for row in cursor.fetchall():
            try:
                pickup_dt = datetime.strptime(row['pickup_date'], '%d/%m/%Y').date()
                if pickup_dt >= today:
                    result[row['shipment_id']] = {'pickup_date': row['pickup_date'], 'marked_at': row['marked_at']}
            except Exception:
                pass
        conn.close()
        return result
    except Exception:
        return {}

def save_treated(data):
    pass

def mark_as_treated(shipment_id, pickup_date):
    conn = get_db()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    conn.execute("INSERT OR REPLACE INTO suivis (shipment_id, pickup_date, marked_at, active) VALUES (?, ?, ?, 1)", (shipment_id, pickup_date, now))
    conn.commit()
    conn.close()

def unmark_treated(shipment_id):
    conn = get_db()
    conn.execute("UPDATE suivis SET active=0 WHERE shipment_id=?", (shipment_id,))
    conn.commit()
    conn.close()

def save_batch_to_db(results_df, meta):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO analyses (date_analyse, periode_debut, periode_fin, total, ignored) VALUES (?, ?, ?, ?, ?)",
        (meta.get('date',''), meta.get('periode_debut',''), meta.get('periode_fin',''), meta.get('total',0), meta.get('ignored',0))
    )
    analyse_id = cursor.lastrowid
    for _, row in results_df.iterrows():
        conn.execute(
            "INSERT INTO resultats (analyse_id, shipment_id, customer_reference, route, carrier_name, business_unit, pickup_date, lead_time, score_risque, rang, priorite, rang_relatif) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (analyse_id, str(row.get('Shipment_ID','')), str(row.get('Customer_Reference','')),
             str(row.get('Route','')), str(row.get('Carrier_Name','')), str(row.get('Business_Unit','')),
             str(row.get('Requested_Pickup_Date','')), row.get('Requested_Lead_Time_Days',0),
             float(row.get('Score_Risque',0)), int(row.get('Rang',0)),
             str(row.get('Priorite',row.get('Priorité',''))), str(row.get('Rang_Relatif','')))
        )
    conn.commit()
    conn.close()

def load_last_batch():
    try:
        conn = get_db()
        last = conn.execute("SELECT * FROM analyses ORDER BY id DESC LIMIT 1").fetchone()
        if not last:
            conn.close()
            return None, None
        rows = conn.execute("SELECT * FROM resultats WHERE analyse_id=? ORDER BY rang", (last['id'],)).fetchall()
        conn.close()
        if not rows:
            return None, None
        df = pd.DataFrame([dict(r) for r in rows]).rename(columns={
            'shipment_id':'Shipment_ID', 'customer_reference':'Customer_Reference',
            'route':'Route', 'carrier_name':'Carrier_Name', 'business_unit':'Business_Unit',
            'pickup_date':'Requested_Pickup_Date', 'lead_time':'Requested_Lead_Time_Days',
            'score_risque':'Score_Risque', 'rang':'Rang', 'priorite':'Priorité', 'rang_relatif':'Rang_Relatif'
        })
        meta = {
            'date':    last['date_analyse'],
            'total':   last['total'],
            'ignored': last['ignored'],
            'periode': f"{last['periode_debut']} - {last['periode_fin']}"
        }
        return df, meta
    except Exception:
        return None, None

# ============================================================
# PREDICTION
# ============================================================
def get_weight_category(weight):
    if weight <= 500:    return 'Light'
    elif weight <= 2000: return 'Medium'
    elif weight <= 5000: return 'Heavy'
    else:                return 'VeryHeavy'

def get_priority_label(rang, total):
    pct = rang / total * 100
    if pct <= 5:                       return 'CRITIQUE'
    elif pct <= 17:                    return 'ELEVE'
    elif pct <= TOP_K / total * 100:   return 'MODERE'
    else:                              return 'STANDARD'

def build_features(carrier, origin, destination, incoterm, bu, service,
                   hazardous, weight, volume, pieces, lead_time,
                   month, year, pickup_dow, delivery_dow):
    route        = f"{origin}→{destination}"
    wcat         = get_weight_category(weight)
    c_stats      = carrier_stats.get(carrier, {'delay_rate': DEFAULT_DELAY_RATE, 'volume': DEFAULT_VOLUME})
    r_stats      = route_stats.get(route,     {'delay_rate': DEFAULT_DELAY_RATE, 'volume': DEFAULT_VOLUME})

    features = {
        'Origin_Country':            ORIGIN_ENC.get(origin, 4),
        'Destination_Country':       DEST_ENC.get(destination, 5),
        'Route':                     ROUTE_ENC.get(route, 39),
        'Carrier_Name':              CARRIER_ENC.get(carrier, 4),
        'Incoterm':                  INCOTERM_ENC.get(incoterm, 3),
        'Gross_Weight_KG':           weight,
        'Gross_Volume_M3':           volume,
        'Number_of_Pieces':          pieces,
        'Requested_Lead_Time_Days':  lead_time,
        'Month':                     month,
        'Year':                      year,
        'Pickup_DayOfWeek':          pickup_dow,
        'Delivery_DayOfWeek':        delivery_dow,
        'Pickup_IsWeekend':          1 if pickup_dow >= 5 else 0,
        'Delivery_IsWeekend':        1 if delivery_dow >= 5 else 0,
        'Business_Unit_ADS':         1 if bu == 'ADS' else 0,
        'Service_Type_RTN':          1 if service == 'RTN' else 0,
        'Hazardous_Y':               1 if str(hazardous).upper() in ['Y','YES','1','TRUE','OUI'] else 0,
        'Weight_Category_Light':     1 if wcat == 'Light'     else 0,
        'Weight_Category_Medium':    1 if wcat == 'Medium'    else 0,
        'Weight_Category_VeryHeavy': 1 if wcat == 'VeryHeavy' else 0,
        'Carrier_Delay_Rate':        c_stats['delay_rate'],
        'Carrier_Volume':            c_stats['volume'],
        'Route_Delay_Rate':          r_stats['delay_rate'],
        'Route_Volume':              r_stats['volume'],
        'Weight_Per_Piece':          weight / max(pieces, 1),
        'Is_Rush':                   1 if lead_time <= 3 else 0,
        'Is_High_Piece_Count':       1 if pieces >= 20 else 0
    }
    return pd.DataFrame([features])[FEATURE_ORDER]

def clean_input(df):
    df = df.copy()
    df['Route'] = df['Origin_Country'].astype(str) + '→' + df['Destination_Country'].astype(str)
    df['Hazardous'] = df['Hazardous'].apply(
        lambda v: 'Y' if str(v).strip().upper() in ['Y','YES','1','TRUE','OUI'] else 'N'
    )
    df['Requested_Pickup_Date']   = pd.to_datetime(df['Requested_Pickup_Date'],   errors='coerce')
    df['Requested_Delivery_Date'] = pd.to_datetime(df['Requested_Delivery_Date'], errors='coerce')

    # Cohérence dates
    mask = (df['Requested_Delivery_Date'].notna() & df['Requested_Pickup_Date'].notna() &
            (df['Requested_Delivery_Date'] < df['Requested_Pickup_Date']))
    if mask.any():
        df.loc[mask, 'Requested_Delivery_Date'] = (
            df.loc[mask, 'Requested_Pickup_Date'] +
            pd.to_timedelta(df.loc[mask, 'Requested_Lead_Time_Days'].fillna(4), unit='d')
        )
    mask2 = df['Requested_Delivery_Date'].isna() & df['Requested_Pickup_Date'].notna()
    if mask2.any():
        df.loc[mask2, 'Requested_Delivery_Date'] = (
            df.loc[mask2, 'Requested_Pickup_Date'] +
            pd.to_timedelta(df.loc[mask2, 'Requested_Lead_Time_Days'].fillna(4), unit='d')
        )

    # Filtre fenêtre J+1 à J+30
    today    = pd.Timestamp(datetime.now().date())
    date_min = today + pd.Timedelta(days=1)
    date_max = today + pd.Timedelta(days=WINDOW_DAYS)
    df = df[df['Requested_Pickup_Date'].between(date_min, date_max)]

    return df

def process_batch(df_input):
    df               = clean_input(df_input)
    results          = []
    ignored          = 0
    unknown_carriers = {}
    unknown_routes   = {}

    for _, row in df.iterrows():
        try:
            pickup   = row['Requested_Pickup_Date']
            delivery = row['Requested_Delivery_Date']
            if pd.isna(pickup):   pickup   = datetime.now()
            if pd.isna(delivery): delivery = pickup

            shipment_id = str(row.get('Shipment_ID', ''))
            carrier = str(row.get('Carrier_Name', 'DHL Express'))
            if carrier not in CARRIER_ENC:
                if carrier not in unknown_carriers:
                    unknown_carriers[carrier] = set()
                unknown_carriers[carrier].add(shipment_id)
                carrier = 'DHL Express'

            route_key = f"{str(row.get('Origin_Country','FR'))}→{str(row.get('Destination_Country','ES'))}"
            if route_key not in ROUTE_ENC:
                if route_key not in unknown_routes:
                    unknown_routes[route_key] = set()
                unknown_routes[route_key].add(shipment_id)

            features = build_features(
                carrier      = carrier,
                origin       = str(row.get('Origin_Country', 'FR')),
                destination  = str(row.get('Destination_Country', 'ES')),
                incoterm     = str(row.get('Incoterm', 'FCA')),
                bu           = str(row.get('Business_Unit', 'AC')),
                service      = str(row.get('Service_Type', 'RTN')),
                hazardous    = str(row.get('Hazardous', 'N')),
                weight       = float(row.get('Gross_Weight_KG', 1000)),
                volume       = float(row.get('Gross_Volume_M3', 1)),
                pieces       = int(row.get('Number_of_Pieces', 5)),
                lead_time    = int(row.get('Requested_Lead_Time_Days', 4)),
                month        = pickup.month,
                year         = pickup.year,
                pickup_dow   = pickup.dayofweek,
                delivery_dow = delivery.dayofweek
            )

            proba = model.predict_proba(scaler.transform(features))[0][1]

            results.append({
                'Shipment_ID':              str(row.get('Shipment_ID', '')),
                'Customer_Reference':       row.get('Customer_Reference', ''),
                'Route':                    row.get('Route', ''),
                'Carrier_Name':             row.get('Carrier_Name', ''),
                'Business_Unit':            row.get('Business_Unit', ''),
                'Requested_Pickup_Date':    pickup.strftime('%d/%m/%Y') if pd.notna(pickup) else '',
                'Requested_Lead_Time_Days': row.get('Requested_Lead_Time_Days', ''),
                'Score_Risque':             round(proba * 100, 1),
            })

        except Exception:
            ignored += 1

    # Log éléments inconnus (cumulatif)
    if unknown_carriers or unknown_routes:
        save_unknown_elements(unknown_carriers, unknown_routes)

    if not results:
        return pd.DataFrame(), ignored

    total  = len(results)
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values('Score_Risque', ascending=False).reset_index(drop=True)
    df_res.insert(0, 'Rang', range(1, total + 1))
    df_res['Rang_Relatif'] = df_res['Rang'].apply(lambda r: f"Top {round(r/total*100)}%")
    df_res['Priorité']     = df_res['Rang'].apply(lambda r: get_priority_label(r, total))

    return df_res, ignored

# ============================================================
# AFFICHAGE
# ============================================================
def format_display(df, sort_by_date=False):
    cols = ['Rang','Priorité','Rang_Relatif','Shipment_ID','Customer_Reference',
            'Route','Carrier_Name','Business_Unit','Requested_Pickup_Date',
            'Requested_Lead_Time_Days','Score_Risque']
    d = df[[c for c in cols if c in df.columns]].copy()
    if sort_by_date and 'Requested_Pickup_Date' in d.columns:
        d = d.iloc[d['Requested_Pickup_Date'].apply(lambda x: pd.to_datetime(x, format='%d/%m/%Y', errors='coerce')).argsort()].reset_index(drop=True)
    d['Score_Risque'] = d['Score_Risque'].apply(lambda x: f"{x}%")
    d = d.rename(columns={
        'Rang_Relatif': 'Classement', 'Shipment_ID': 'Shipment',
        'Customer_Reference': 'Référence', 'Carrier_Name': 'Transporteur',
        'Business_Unit': 'BU', 'Requested_Pickup_Date': 'Date Pickup',
        'Requested_Lead_Time_Days': 'Lead Time', 'Score_Risque': 'Score Risque'
    })
    return d

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("""
<div style='text-align:center; padding:1.5rem 0 2rem 0;'>
    <div style='font-size:1.6rem; font-weight:800; letter-spacing:2px;'>CEVA</div>
    <div style='font-size:0.75rem; letter-spacing:3px; opacity:0.7;'>LOGISTICS</div>
</div>
""", unsafe_allow_html=True)

page = st.sidebar.radio("", ["Analyse", "Vue analytique", "Documentation"])

# ============================================================
# PAGE ANALYSE
# ============================================================
if page == "Analyse":

    st.markdown("""
    <div class="page-header">
        <h2>Analyse des Risques de Retard</h2>
        <p>Classement des expéditions planifiées par niveau de risque — fenêtre J+1 à J+30</p>
    </div>
    """, unsafe_allow_html=True)

    template_cols = ['Shipment_ID','Customer_Reference','Carrier_Name','Origin_Country',
                     'Destination_Country','Business_Unit','Service_Type','Hazardous',
                     'Incoterm','Gross_Weight_KG','Gross_Volume_M3','Number_of_Pieces',
                     'Requested_Lead_Time_Days','Requested_Pickup_Date','Requested_Delivery_Date',
                     'Actual_Pickup_Date']
    template_csv = pd.DataFrame({col:[''] for col in template_cols}).to_csv(index=False).encode('utf-8')

    col_up, col_tpl = st.columns([3, 1])
    with col_up:
        uploaded_file = st.file_uploader("Charger le fichier d'expéditions planifiées (CSV)", type=['csv'])
    with col_tpl:
        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button("Télécharger le template", data=template_csv,
                           file_name="template_upload.csv", mime='text/csv',
                           use_container_width=True)

    if uploaded_file:
        df_input = pd.read_csv(uploaded_file)
        if 'Actual_Pickup_Date' in df_input.columns:
            df_input = df_input[
                df_input['Actual_Pickup_Date'].isna() |
                df_input['Actual_Pickup_Date'].astype(str).str.strip().isin(['', 'nan', 'NaN', 'NaT'])
            ].copy()

        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"{len(df_input)} expéditions détectées dans le fichier")
        with col2:
            run = st.button("Lancer l'analyse", use_container_width=True)

        if run:
            with st.spinner("Analyse en cours..."):
                results_df, n_ignored = process_batch(df_input)
                try:
                    dates  = pd.to_datetime(df_input['Requested_Pickup_Date'], errors='coerce').dropna()
                    periode = f"{dates.min().strftime('%d/%m/%Y')} — {dates.max().strftime('%d/%m/%Y')}"
                except:
                    periode = "N/A"
                meta = {
                    'date':          datetime.now().strftime("%d/%m/%Y %H:%M"),
                    'total':         len(results_df),
                    'ignored':       n_ignored,
                    'periode':       periode,
                    'periode_debut': periode.split(' - ')[0] if ' - ' in periode else periode,
                    'periode_fin':   periode.split(' - ')[1] if ' - ' in periode else ''
                }
                save_batch_to_db(results_df, meta)
                st.session_state['results'] = results_df
                st.session_state['meta']    = meta
            st.rerun()

    if 'results' not in st.session_state and DB_PATH.exists():
        df, meta = load_last_batch()
        if df is not None:
            st.session_state['results'] = df
            st.session_state['meta']    = meta

    if 'results' in st.session_state:
        results  = st.session_state['results']
        meta     = st.session_state.get('meta', {})
        total    = len(results)
        treated  = load_treated()

        # S'assurer que Shipment_ID est string
        results['Shipment_ID'] = results['Shipment_ID'].astype(str)

        ignored_txt = f" — {meta.get('ignored',0)} ligne(s) ignorée(s)" if meta.get('ignored', 0) > 0 else ""
        st.markdown(f"""
        <div class="summary-bar">
            <strong>{total}</strong> expéditions analysées &nbsp;|&nbsp;
            Période : {meta.get('periode','N/A')} &nbsp;|&nbsp;
            Mise à jour : {meta.get('date','N/A')}{ignored_txt}
        </div>
        """, unsafe_allow_html=True)

        # Alerte éléments inconnus
        unknown_log = load_unknown_log()
        nb_carriers = len(unknown_log.get("transporteurs_inconnus", {}))
        nb_routes   = len(unknown_log.get("routes_inconnues", {}))
        if nb_carriers > 0 or nb_routes > 0:
            parts = []
            if nb_carriers > 0: parts.append(f"{nb_carriers} transporteur(s) non reconnu(s)")
            if nb_routes   > 0: parts.append(f"{nb_routes} route(s) non reconnue(s)")
            st.warning(f"{' et '.join(parts)} — traités avec le taux de retard moyen (27%). Voir Documentation pour le détail.")

        # Séparer traités / non traités
        treated_ids     = set(treated.keys())
        untreated       = results[~results['Shipment_ID'].isin(treated_ids)].copy()
        treated_df      = results[results['Shipment_ID'].isin(treated_ids)].copy()

        top50_untreated = untreated.head(TOP_K)
        top50_treated   = treated_df
        rest            = untreated.iloc[TOP_K:]

        # TOP 50 — interventions actives
        nb_active = len(top50_untreated)
        st.markdown(f'<p class="section-label">Interventions prioritaires — {nb_active} expéditions</p>', unsafe_allow_html=True)

        if len(top50_untreated) > 0:
            for _, row in top50_untreated.iterrows():
                col_data, col_btn = st.columns([10, 1])
                with col_data:
                    st.dataframe(
                        format_display(pd.DataFrame([row])),
                        use_container_width=True, hide_index=True
                    )
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Traité", key=f"treat_{row['Shipment_ID']}"):
                        mark_as_treated(row['Shipment_ID'], row['Requested_Pickup_Date'])
                        st.rerun()

        # SUIVIS EN COURS
        if len(top50_treated) > 0:
            st.markdown(f'<p class="section-label-secondary">Suivis en cours — {len(top50_treated)}</p>', unsafe_allow_html=True)
            for _, row in top50_treated.iterrows():
                col_data, col_btn = st.columns([10, 1])
                with col_data:
                    d = format_display(pd.DataFrame([row]))
                    st.dataframe(d, use_container_width=True, hide_index=True)
                with col_btn:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Retirer", key=f"untreat_{row['Shipment_ID']}"):
                        unmark_treated(row['Shipment_ID'])
                        st.rerun()

        # RESTANTES
        if len(rest) > 0:
            st.markdown(f'<p class="section-label-secondary">Expéditions restantes — {len(rest)}</p>', unsafe_allow_html=True)
            st.dataframe(format_display(rest, sort_by_date=True), use_container_width=True, hide_index=True)

        st.markdown("---")
        export = results.copy()
        export['Score_Risque'] = export['Score_Risque'].apply(lambda x: f"{x}%")
        st.download_button("Télécharger le fichier complet",
                           data=export.to_csv(index=False).encode('utf-8'),
                           file_name=f"analyse_risques_{datetime.now().strftime('%Y%m%d')}.csv",
                           mime='text/csv')

    elif not uploaded_file:
        st.markdown("<div style='text-align:center; padding:3rem; color:#888;'>Chargez un fichier CSV pour démarrer l'analyse.</div>",
                    unsafe_allow_html=True)

# ============================================================
# PAGE VUE ANALYTIQUE
# ============================================================
elif page == "Vue analytique":

    st.markdown("""
    <div class="page-header">
        <h2>Vue analytique</h2>
        <p>Agrégation des risques par carrier, route et horizon temporel</p>
    </div>
    """, unsafe_allow_html=True)

    # Charger les résultats
    if 'results' not in st.session_state and DB_PATH.exists():
        df, meta = load_last_batch()
        if df is not None:
            st.session_state['results'] = df
            st.session_state['meta']    = meta

    if 'results' not in st.session_state:
        st.markdown("<div style='text-align:center; padding:3rem; color:#888;'>Aucune analyse disponible. Chargez un fichier depuis la page Analyse.</div>",
                    unsafe_allow_html=True)
    else:
        results  = st.session_state['results']
        treated  = load_treated()
        results['Shipment_ID'] = results['Shipment_ID'].astype(str)

        # Top 50 actif uniquement (non traités)
        top50 = results[
            (results['Rang'] <= TOP_K) &
            (~results['Shipment_ID'].isin(treated.keys()))
        ].copy()

        total_top50 = len(top50)

        # ── MÉTRIQUES CLÉS ───────────────────────────────────────
        st.markdown('<p class="section-label">Métriques clés</p>', unsafe_allow_html=True)

        carriers_at_risk = top50['Carrier_Name'].nunique()
        routes_at_risk   = top50['Route'].nunique()

        # Semaine la plus chargée
        top50['_pickup'] = pd.to_datetime(top50['Requested_Pickup_Date'], format='%d/%m/%Y', errors='coerce')
        top50['_week']   = top50['_pickup'].dt.isocalendar().week
        if top50['_week'].notna().any():
            busiest_week_num  = top50['_week'].value_counts().idxmax()
            busiest_week_mask = top50['_week'] == busiest_week_num
            busiest_date      = top50.loc[busiest_week_mask, '_pickup'].min()
            busiest_label     = f"Sem. du {busiest_date.strftime('%d/%m')}" if pd.notna(busiest_date) else "N/A"
            busiest_count     = busiest_week_mask.sum()
        else:
            busiest_label = "N/A"
            busiest_count = 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Interventions prioritaires", total_top50)
        col2.metric("Carriers concernés",         carriers_at_risk)
        col3.metric("Routes concernées",           routes_at_risk)
        col4.metric("Pic de risque",               busiest_label, help=f"{busiest_count} shipments à risque cette semaine")

        st.markdown("---")

        # ── CARRIERS ET ROUTES ───────────────────────────────────
        st.markdown('<p class="section-label">Répartition dans le Top 50</p>', unsafe_allow_html=True)

        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("**Par transporteur**")
            carrier_counts = (
                top50.groupby('Carrier_Name')
                .size()
                .reset_index(name='Shipments Top 50')
                .sort_values('Shipments Top 50', ascending=False)
            )
            # Ajouter taux historique
            carrier_counts['Taux retard historique'] = carrier_counts['Carrier_Name'].apply(
                lambda c: f"{round(carrier_stats.get(c, {}).get('delay_rate', DEFAULT_DELAY_RATE) * 100, 1)}%"
            )
            carrier_counts = carrier_counts.rename(columns={'Carrier_Name': 'Transporteur'})
            st.dataframe(carrier_counts, use_container_width=True, hide_index=True)

        with col_right:
            st.markdown("**Par route**")
            route_counts = (
                top50.groupby('Route')
                .size()
                .reset_index(name='Shipments Top 50')
                .sort_values('Shipments Top 50', ascending=False)
            )
            route_counts['Taux retard historique'] = route_counts['Route'].apply(
                lambda r: f"{round(route_stats.get(r, {}).get('delay_rate', DEFAULT_DELAY_RATE) * 100, 1)}%"
            )
            st.dataframe(route_counts, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── DISTRIBUTION TEMPORELLE ───────────────────────────────
        st.markdown('<p class="section-label">Distribution temporelle</p>', unsafe_allow_html=True)

        today    = pd.Timestamp(datetime.now().date())
        bins     = [
            ("J+1 à J+7",   today + pd.Timedelta(days=1),  today + pd.Timedelta(days=7)),
            ("J+8 à J+14",  today + pd.Timedelta(days=8),  today + pd.Timedelta(days=14)),
            ("J+15 à J+30", today + pd.Timedelta(days=15), today + pd.Timedelta(days=30)),
        ]

        dist_data = []
        for label, d_min, d_max in bins:
            count = top50['_pickup'].between(d_min, d_max).sum()
            dist_data.append({"Horizon": label, "Shipments à risque": int(count)})

        st.dataframe(pd.DataFrame(dist_data), use_container_width=True, hide_index=True)

        st.caption("Cette vue est basée sur les interventions prioritaires actives (hors suivis en cours).")

# ============================================================
# PAGE DOCUMENTATION
# ============================================================
elif page == "Documentation":

    st.markdown("""
    <div class="page-header">
        <h2>Documentation</h2>
        <p>Méthodologie et utilisation du système</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Contexte")
    st.markdown("""
    Ce système prédit le risque de retard des expéditions aériennes sur le contrat Airbus
    afin de permettre aux équipes opérationnelles de prioriser leurs interventions préventives.
    Seules les expéditions dont la date de pickup est comprise entre J+1 et J+30 sont analysées.
    """)

    st.markdown("---")
    st.markdown("### Performances")
    col1, col2, col3 = st.columns(3)
    col1.metric("Precision Top 50", "67.7%", help="7 alertes sur 10 correspondent à de vrais retards")
    col2.metric("Recall Top 50",    "42.2%", help="40% des retards réels détectés")
    col3.metric("Dataset",          "~30 000 expéditions")
    st.markdown("""
    Le modèle classe les expéditions par ordre de risque décroissant. Les 50 premières constituent
    les interventions prioritaires recommandées. Cette configuration garantit que 7 alertes sur 10
    correspondent à de vrais retards, tout en maintenant une charge de supervision maîtrisée.
    """)

    st.markdown("---")
    st.markdown("### Utilisation")
    st.markdown("""
    Les équipes CBS exportent quotidiennement depuis le TMS la liste des expéditions planifiées
    non encore pickées, avec une fenêtre de pickup de J+1 à J+30, et chargent ce fichier dans
    l'application. Le classement produit reste disponible pour l'ensemble des équipes jusqu'au
    prochain upload. Le template de fichier est téléchargeable directement depuis la page Analyse.

    Les superviseurs peuvent marquer une expédition comme "Traitée" directement dans le tableau.
    Elle est alors déplacée dans la section "Suivis en cours" et n'encombre plus la liste des
    interventions prioritaires. Le marquage expire automatiquement à la date de pickup prévue.
    """)

    st.markdown("---")
    st.markdown("### Niveaux de priorité")
    st.markdown("""
    Les expéditions du Top 50 sont classées en trois niveaux selon leur rang relatif dans
    l'ensemble du portefeuille analysé.

    **CRITIQUE** — Top 5%

    **ELEVE** — Top 6% à 17%

    **MODERE** — Top 18% à 50

    Les expéditions au-delà du Top 50 sont classées **STANDARD** et triées par date de pickup.
    """)

    st.markdown("---")
    st.markdown("### Éléments non reconnus")
    unknown_log = load_unknown_log()
    nb_carriers = len(unknown_log.get("transporteurs_inconnus", {}))
    nb_routes   = len(unknown_log.get("routes_inconnues", {}))

    if nb_carriers == 0 and nb_routes == 0:
        st.success("Aucun élément non reconnu détecté sur les dernières analyses.")
    else:
        if unknown_log.get("derniere_mise_a_jour"):
            st.caption(f"Dernière mise à jour : {unknown_log['derniere_mise_a_jour']}")
        if nb_carriers > 0:
            st.markdown("**Transporteurs non reconnus**")
            st.dataframe(pd.DataFrame([{"Transporteur": k, "Shipments concernés": len(v)}
                for k, v in sorted(unknown_log["transporteurs_inconnus"].items(), key=lambda x: len(x[1]), reverse=True)]),
                use_container_width=True, hide_index=True)
        if nb_routes > 0:
            st.markdown("**Routes non reconnues**")
            st.dataframe(pd.DataFrame([{"Route": k, "Shipments concernés": len(v)}
                for k, v in sorted(unknown_log["routes_inconnues"].items(), key=lambda x: len(x[1]), reverse=True)]),
                use_container_width=True, hide_index=True)
        st.info("Ces éléments ont été traités avec le taux de retard moyen (27%). Leur apparition fréquente signale un besoin de mise à jour du référentiel.")
        if st.button("Réinitialiser le log"):
            save_unknown_log({"transporteurs_inconnus": {}, "routes_inconnues": {}})
            st.rerun()

    st.markdown("---")
    st.markdown("### Limites")
    st.warning("""
    Le modèle repose sur des patterns historiques. Il ne peut pas anticiper des événements
    exceptionnels comme les grèves, les aléas météorologiques ou les tensions géopolitiques.
    Un réentraînement périodique est recommandé pour maintenir la pertinence des prédictions.
    """)

    st.markdown("---")
    st.markdown("### Conformité RGPD")
    st.success("""
    Le système ne traite aucune donnée à caractère personnel. Les variables utilisées
    sont exclusivement opérationnelles et logistiques.
    """)
