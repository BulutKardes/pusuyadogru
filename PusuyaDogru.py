import math
import sqlite3
import numpy as np
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
import folium
from streamlit_folium import st_folium

# ==============================================================================
# 1. SAYFA VE TEMA YAPILANDIRMASI
# ==============================================================================
st.set_page_config(
    page_title="Pusuya Doğru - Kuantum Keşif",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #070510 0%, #0f0a21 50%, #080312 100%);
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .hero-container {
        text-align: center;
        padding: 1.2rem 0.8rem;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 243, 255, 0.15);
        border-radius: 20px;
        margin-bottom: 1rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    }
    .hero-title {
        background: linear-gradient(90deg, #00f3ff, #9d4edd, #ff007f);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin: 0;
    }
    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.85rem;
        margin-top: 6px;
    }
    .quantum-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(0, 243, 255, 0.18);
        border-radius: 16px;
        padding: 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
    }
    .stButton > button {
        background: linear-gradient(135deg, #7b2cbf 0%, #3a0ca3 50%, #4cc9f0 100%);
        color: #ffffff;
        border: none;
        border-radius: 14px;
        padding: 0.75rem 1.2rem;
        font-weight: 700;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 20px rgba(123, 44, 191, 0.4);
        transition: all 0.2s ease-in-out;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 243, 255, 0.6);
        color: #ffffff;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: rgba(255, 255, 255, 0.03);
        padding: 6px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        border-radius: 12px;
        color: #94a3b8;
        font-size: 0.88rem;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0, 243, 255, 0.15) !important;
        color: #00f3ff !important;
        border: 1px solid rgba(0, 243, 255, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# GİZLİ ADMIN ŞİFRESİ (Streamlit Secrets'tan okunur, yoksa 22027 varsayılan alınır)
ADMIN_PASSKEY = st.secrets.get("ADMIN_KEY", "22027")

# ==============================================================================
# 2. VERİTABANI YÖNETİMİ (KEY İZOLASYONLU)
# ==============================================================================
DB_FILE = "quantum_discoveries.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Kullanıcı Erişim Keyleri Tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS access_keys (
            access_key TEXT PRIMARY KEY,
            created_at TEXT,
            note TEXT
        )
    ''')

    # 2. Tablo yapısı güncellemeleri (Migration)
    # discoveries tablosunu kontrol et ve güncelle
    c.execute("PRAGMA table_info(discoveries)")
    columns = [column[1] for column in c.fetchall()]
    if columns and "access_key" not in columns:
        if "device_id" in columns:
            c.execute("ALTER TABLE discoveries RENAME COLUMN device_id TO access_key")
        else:
            c.execute("ALTER TABLE discoveries ADD COLUMN access_key TEXT")

    # saved_locations tablosunu kontrol et ve güncelle
    c.execute("PRAGMA table_info(saved_locations)")
    columns = [column[1] for column in c.fetchall()]
    if columns and "access_key" not in columns:
        if "device_id" in columns:
            c.execute("ALTER TABLE saved_locations RENAME COLUMN device_id TO access_key")
        else:
            c.execute("ALTER TABLE saved_locations ADD COLUMN access_key TEXT")

    # user_settings tablosunu kontrol et ve güncelle
    c.execute("PRAGMA table_info(user_settings)")
    columns = [column[1] for column in c.fetchall()]
    if columns and "access_key" not in columns:
        if "device_id" in columns:
            c.execute("ALTER TABLE user_settings RENAME COLUMN device_id TO access_key")
        else:
            c.execute("ALTER TABLE user_settings ADD COLUMN access_key TEXT")

    # 3. Tablolar yoksa sıfırdan oluştur
    c.execute('''
        CREATE TABLE IF NOT EXISTS discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_key TEXT,
            timestamp TEXT,
            lat REAL,
            lon REAL,
            anomaly_type TEXT,
            power REAL,
            intent TEXT,
            notes TEXT,
            ai_interpretation TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS saved_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            access_key TEXT,
            name TEXT,
            lat REAL,
            lon REAL,
            UNIQUE(access_key, name)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            access_key TEXT PRIMARY KEY,
            groq_key TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def is_key_valid(key):
    if key == ADMIN_PASSKEY:
        return True
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT access_key FROM access_keys WHERE access_key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row is not None

def add_access_key(key, note=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO access_keys (access_key, created_at, note) VALUES (?, ?, ?)", (key, now, note))
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    conn.close()
    return success

def get_all_access_keys():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM access_keys ORDER BY created_at DESC", conn)
    conn.close()
    return df

def delete_access_key(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM access_keys WHERE access_key = ?", (key,))
    conn.commit()
    conn.close()

def save_discovery(key, lat, lon, anomaly_type, power, intent, notes, ai_interpretation):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO discoveries (access_key, timestamp, lat, lon, anomaly_type, power, intent, notes, ai_interpretation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (key, now, lat, lon, anomaly_type, power, intent, notes, ai_interpretation))
    conn.commit()
    conn.close()

def get_all_discoveries(key):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM discoveries WHERE access_key = ? ORDER BY id DESC", conn, params=(key,))
    conn.close()
    return df

def delete_discovery(key, entry_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM discoveries WHERE id = ? AND access_key = ?", (entry_id, key))
    conn.commit()
    conn.close()

def save_custom_location(key, name, lat, lon):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO saved_locations (access_key, name, lat, lon) 
        VALUES (?, ?, ?, ?)
    ''', (key, name, lat, lon))
    conn.commit()
    conn.close()

def get_saved_locations(key):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM saved_locations WHERE access_key = ? ORDER BY name ASC", conn, params=(key,))
    conn.close()
    return df

def delete_saved_location(key, loc_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM saved_locations WHERE id = ? AND access_key = ?", (loc_id, key))
    conn.commit()
    conn.close()

def save_groq_key(key, groq_key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO user_settings (access_key, groq_key) VALUES (?, ?)
    ''', (key, groq_key))
    conn.commit()
    conn.close()

def get_groq_key(key):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT groq_key FROM user_settings WHERE access_key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else ""

init_db()

# ==============================================================================
# 3. KULLANICI GİRİŞİ & OTURUM KONTROLÜ
# ==============================================================================
if "authenticated_key" not in st.session_state:
    st.session_state.authenticated_key = None

if not st.session_state.authenticated_key:
    st.markdown("""
    <div class="hero-container" style="max-width: 450px; margin: 50px auto;">
        <h1 class="hero-title">🔮 PUSUYA DOĞRU</h1>
        <p class="hero-subtitle">Erişim Sağlamak İçin Lütfen Key Giriniz</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_auth1, col_auth2, col_auth3 = st.columns([1, 2, 1])
    with col_auth2:
        input_key = st.text_input("Erişim Key / Admin Şifresi:", type="password", key="login_key_input")
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if is_key_valid(input_key.strip()):
                st.session_state.authenticated_key = input_key.strip()
                st.toast("🔑 Giriş Başarılı!", icon="✅")
                st.rerun()
            else:
                st.error("❌ Geçersiz Key veya Şifre!")
    st.stop()

CURRENT_KEY = st.session_state.authenticated_key
IS_ADMIN = (CURRENT_KEY == ADMIN_PASSKEY)

# ==============================================================================
# 4. SESSION STATE İLK YÜKLEME
# ==============================================================================
if "user_lat" not in st.session_state:
    st.session_state.user_lat = 41.2867
if "user_lon" not in st.session_state:
    st.session_state.user_lon = 36.3300
if "input_lat" not in st.session_state:
    st.session_state.input_lat = st.session_state.user_lat
if "input_lon" not in st.session_state:
    st.session_state.input_lon = st.session_state.user_lon
if "active_point" not in st.session_state:
    st.session_state.active_point = None
if "groq_key" not in st.session_state:
    st.session_state.groq_key = get_groq_key(CURRENT_KEY)

# ==============================================================================
# 5. KUANTUM ENTROPİ & AI MOTORU
# ==============================================================================
def get_quantum_random_numbers(count=100):
    url = f"https://qrng.anu.edu.au/API/jsonI.php?length={count}&type=hex16&size=1"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                hex_list = data["data"]
                return np.array([int(h, 16) / 65535.0 for h in hex_list])
    except Exception:
        pass
    return np.random.uniform(0, 1, count)

def generate_quantum_point(center_lat, center_lon, radius_km, mode="Attractor"):
    q_data = get_quantum_random_numbers(150)
    lat_deg_per_km = 1 / 111.0
    lon_deg_per_km = 1 / (111.0 * math.cos(math.radians(center_lat)))
    
    u, v, weights = q_data[:50], q_data[50:100], q_data[100:150]
    radii = radius_km * np.sqrt(u)
    angles = 2 * math.pi * v
    
    dx = radii * np.cos(angles) * lon_deg_per_km
    dy = radii * np.sin(angles) * lat_deg_per_km
    
    lats = center_lat + dy
    lons = center_lon + dx
    
    if mode == "Attractor":
        idx = np.argmax(weights)
        power = round(float(np.max(weights) * 9.5 + 1.2), 2)
    elif mode == "Void":
        idx = np.argmin(weights)
        power = round(float((1 - np.min(weights)) * 8.5 + 1.0), 2)
    else:
        idx = np.random.randint(0, len(lats))
        power = round(float(np.random.uniform(1.5, 6.0)), 2)
        
    return lats[idx], lons[idx], power

def analyze_intent_with_groq(api_key, intent, anomaly_type, power, notes=""):
    if not api_key:
        return "⚠️ Lütfen Ayarlar sekmesinden geçerli bir Groq API anahtarı girin."
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    prompt = f"""
    Sen 'Pusuya Doğru' adlı kuantum keşif ve senkronisite rehberisin.
    Kullanıcının Niyeti: "{intent}"
    Anomali Tipi: {anomaly_type}
    Güç: {power} / 10
    Notlar: "{notes}"
    Lütfen bu keşif gezisi için mistik, psikolojik ve senkronisite odaklı derin bir yorum yap (3-4 paragraf).
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Sen bilge bir kuantum keşif rehberisin."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        return f"API Hatası ({res.status_code}): {res.text}"
    except Exception as e:
        return f"Bağlantı hatası: {str(e)}"

# ==============================================================================
# 6. ANA ARAYÜZ VE SEKMELER
# ==============================================================================
top_col1, top_col2 = st.columns([8, 2])
with top_col1:
    st.markdown(f"##### 🔑 Aktif Key: `{CURRENT_KEY if not IS_ADMIN else 'ADMIN MODU'}`")
with top_col2:
    if st.button("🔴 Çıkış Yap"):
        st.session_state.authenticated_key = None
        st.rerun()

st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">🔮 PUSUYA DOĞRU</h1>
    <p class="hero-subtitle">Kuantum Entropi Keşif & Anomali Tarayıcı</p>
</div>
""", unsafe_allow_html=True)

# Sekme Listesi Yapılandırması (Admin modunda Key Ekle sekmesi açılır)
tabs_list = ["📍 Keşif Haritası", "🤖 AI Niyet Analizi", "📜 Keşif Günlüğü", "⚙️ Ayarlar"]
if IS_ADMIN:
    tabs_list.append("🔑 Key Üreteci (Admin)")

active_tabs = st.tabs(tabs_list)

# ------------------------------------------------------------------------------
# TAB 1: KEŞİF HARİTASI
# ------------------------------------------------------------------------------
with active_tabs[0]:
    saved_df = get_saved_locations(CURRENT_KEY)
    if not saved_df.empty:
        loc_options = {"-- Kayıtlı Konum Seçin (Otomatik Doldur) --": None}
        for _, row in saved_df.iterrows():
            loc_options[f"⭐ {row['name']} ({row['lat']:.4f}, {row['lon']:.4f})"] = (row['lat'], row['lon'])
        
        selected_loc_name = st.selectbox("📍 Bu Key'e Özel Kayıtlı Konumlar:", list(loc_options.keys()))
        if selected_loc_name and loc_options[selected_loc_name] is not None:
            t_lat, t_lon = loc_options[selected_loc_name]
            if st.session_state.user_lat != t_lat or st.session_state.user_lon != t_lon:
                st.session_state.user_lat = t_lat
                st.session_state.user_lon = t_lon
                st.session_state.input_lat = t_lat
                st.session_state.input_lon = t_lon
                st.toast(f"🎯 '{selected_loc_name}' yüklendi.", icon="✅")
                st.rerun()

    with st.expander("🎯 Kuantum Parametreleri & Koordinat", expanded=True):
        st.markdown(f"**Aktif Koordinat:** `{st.session_state.user_lat:.5f}, {st.session_state.user_lon:.5f}`")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            anomaly_type = st.radio("Anomali Türü:", ["Attractor (Yoğunluk)", "Void (Boşluk)", "Blindspot (Kör Nokta)"], index=0)
        with col_m2:
            search_radius = st.slider("Arama Yarıçapı (km):", min_value=1.0, max_value=15.0, value=3.0, step=0.5)
            user_intent_input = st.text_input("Niyetiniz / Odak Noktanız:", placeholder="Örn: Huzur, Yeni bir işaret...")

    if st.button("🌌 KUANTUM ANOMALİSİ ÜRET", use_container_width=True):
        with st.spinner("Kuantum entropi havuzuna bağlanılıyor..."):
            mode_clean = anomaly_type.split()[0]
            lat, lon, power = generate_quantum_point(st.session_state.user_lat, st.session_state.user_lon, search_radius, mode=mode_clean)
            st.session_state.active_point = {
                "lat": lat, "lon": lon, "power": power, "type": mode_clean,
                "intent": user_intent_input if user_intent_input else "Belirtilmedi", "radius": search_radius
            }
            st.toast("✨ Yeni Kuantum Koordinatı Tespiti Yapıldı!", icon="🎯")

    st.markdown("<h4 style='color:#00f3ff; margin-top:10px;'>🗺️ Canlı Kuantum Sahası</h4>", unsafe_allow_html=True)
    m = folium.Map(location=[st.session_state.user_lat, st.session_state.user_lon], zoom_start=13, tiles="CartoDB dark_matter")
    folium.Marker([st.session_state.user_lat, st.session_state.user_lon], popup="Başlangıç Konumunuz", icon=folium.Icon(color="blue", icon="user", prefix="fa")).add_to(m)

    if st.session_state.active_point:
        apt = st.session_state.active_point
        folium.Circle(radius=180, location=[apt["lat"], apt["lon"]], color="#00f3ff", fill=True, fill_color="#9d4edd", fill_opacity=0.45).add_to(m)
        folium.Marker([apt["lat"], apt["lon"]], popup=f"Güç: {apt['power']} | Tip: {apt['type']}", icon=folium.Icon(color="red", icon="bullseye", prefix="fa")).add_to(m)

    st_folium(m, width="100%", height=360, returned_objects=[])

    if st.session_state.active_point:
        apt = st.session_state.active_point
        st.markdown(f"""
        <div class="quantum-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #00f3ff; font-weight: bold; font-size:1.1rem;">⚡ {apt['type'].upper()} ANOMALİSİ</span>
                <span style="background: rgba(157, 78, 221, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #9d4edd; color:#e2e8f0;">Güç: {apt['power']}</span>
            </div>
            <p style="margin: 10px 0 5px 0; font-size: 0.9rem; color: #cbd5e1;">
                <b>Hedef Koordinatlar:</b> {apt['lat']:.5f}, {apt['lon']:.5f}<br>
                <b>Belirlenen Niyet:</b> {apt['intent']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&origin={st.session_state.user_lat},{st.session_state.user_lon}&destination={apt['lat']},{apt['lon']}"
        st.markdown(f'<a href="{gmaps_url}" target="_blank" style="text-decoration: none;"><button style="background: linear-gradient(90deg, #10b981, #059669); color: white; width: 100%; border-radius: 12px; padding: 12px; border: none; font-weight: bold; margin-bottom: 15px; cursor: pointer;">🧭 Google Maps ile Rotayı Başlat</button></a>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: AI NİYET ANALİZİ
# ------------------------------------------------------------------------------
with active_tabs[1]:
    st.markdown("<h4 style='color:#9d4edd;'>🤖 AI Kuantum Rehberi</h4>", unsafe_allow_html=True)
    if not st.session_state.active_point:
        st.info("ℹ️ Henüz aktif bir kuantum noktası üretmediniz.")
    else:
        apt = st.session_state.active_point
        st.write(f"**Aktif Hedef:** {apt['type']} (Güç: {apt['power']}) | **Niyet:** {apt['intent']}")
        user_notes = st.text_area("Gözlemleriniz / Hisleriniz:", placeholder="Oraya vardığınızda hissettiklerinizi yazın...")
        
        if st.button("🔮 Niyeti & Senkronisiteyi Yorumla", use_container_width=True):
            with st.spinner("Groq AI analiz ediyor..."):
                ai_res = analyze_intent_with_groq(st.session_state.groq_key, apt['intent'], apt['type'], apt['power'], user_notes)
                st.session_state["last_ai_res"] = ai_res
        
        if "last_ai_res" in st.session_state:
            st.markdown(f'<div class="quantum-card" style="border-color: #9d4edd;"><h5 style="color: #00f3ff; margin-top:0;">✨ Groq AI Senkronisite Analizi</h5><div style="font-size: 0.95rem; line-height: 1.6; color: #e2e8f0;">{st.session_state["last_ai_res"]}</div></div>', unsafe_allow_html=True)
            if st.button("💾 Bu Keşfi Key'inize Kaydet"):
                save_discovery(CURRENT_KEY, apt['lat'], apt['lon'], apt['type'], apt['power'], apt['intent'], user_notes, st.session_state["last_ai_res"])
                st.success("Keşif Key'inize özel olarak kaydedildi!")

# ------------------------------------------------------------------------------
# TAB 3: KEŞİF GÜNLÜĞÜ
# ------------------------------------------------------------------------------
with active_tabs[2]:
    st.markdown("<h4 style='color:#00f3ff;'>📜 Keşif Günlüğü</h4>", unsafe_allow_html=True)
    discoveries_df = get_all_discoveries(CURRENT_KEY)
    if discoveries_df.empty:
        st.info("Bu Key ile kaydedilmiş bir keşif bulunmuyor.")
    else:
        for idx, row in discoveries_df.iterrows():
            st.markdown(f"""
            <div class="quantum-card">
                <div style="display:flex; justify-content:space-between;">
                    <span style="color:#00f3ff; font-weight:bold;">{row['anomaly_type']} Noktası</span>
                    <small style="color:#94a3b8;">{row['timestamp']}</small>
                </div>
                <p style="margin:6px 0; font-size:0.88rem; color:#cbd5e1;">
                    <b>Niyet:</b> {row['intent']} | <b>Güç:</b> {row['power']}<br>
                    <b>Notlar:</b> {row['notes'] if row['notes'] else 'Not yok.'}
                </p>
            </div>
            """, unsafe_allow_html=True)
            with st.expander("AI Yorumu / Detaylar"):
                st.write(row['ai_interpretation'] if row['ai_interpretation'] else "Yorum yok.")
                if st.button(f"🗑️ Kaydı Sil #{row['id']}", key=f"del_{row['id']}"):
                    delete_discovery(CURRENT_KEY, row['id'])
                    st.rerun()

# ------------------------------------------------------------------------------
# TAB 4: AYARLAR
# ------------------------------------------------------------------------------
with active_tabs[3]:
    st.markdown("<h4 style='color:#ff007f;'>⚙️ Sistem ve Konum Ayarları</h4>", unsafe_allow_html=True)
    groq_input = st.text_input("Groq API Key (Bu Key için saklanır):", value=st.session_state.groq_key, type="password")
    if groq_input != st.session_state.groq_key:
        st.session_state.groq_key = groq_input
        save_groq_key(CURRENT_KEY, groq_input)
        st.success("API Key bu Key hesabı için kaydedildi!")

    st.divider()
    st.subheader("📍 Başlangıç Koordinatları")
    c1, c2 = st.columns(2)
    with c1:
        new_lat = st.number_input("Enlem:", value=st.session_state.input_lat, format="%.5f", key="num_lat_input")
    with c2:
        new_lon = st.number_input("Boylam:", value=st.session_state.input_lon, format="%.5f", key="num_lon_input")
        
    if st.button("📍 Koordinatları Aktif Yap"):
        st.session_state.user_lat, st.session_state.user_lon = new_lat, new_lon
        st.session_state.input_lat, st.session_state.input_lon = new_lat, new_lon
        st.success("Konum güncellendi!")

    st.markdown("---")
    st.subheader("⭐ Bu Key Hesabına Konum Kaydet")
    loc_name_input = st.text_input("Konum İsmi:", placeholder="Örn: Ev, Sahil...")
    if st.button("💾 Konumu Kaydet"):
        if loc_name_input.strip():
            save_custom_location(CURRENT_KEY, loc_name_input.strip(), new_lat, new_lon)
            st.success(f"'{loc_name_input}' bu Key'e kaydedildi!")
            st.rerun()
        else:
            st.warning("İsim giriniz.")

    saved_df_manage = get_saved_locations(CURRENT_KEY)
    if not saved_df_manage.empty:
        st.subheader("🗑️ Kayıtlı Konumları Yönet")
        for idx, r in saved_df_manage.iterrows():
            col_l1, col_l2 = st.columns([3, 1])
            with col_l1:
                st.write(f"**{r['name']}** ({r['lat']:.4f}, {r['lon']:.4f})")
            with col_l2:
                if st.button("Sil", key=f"del_loc_{r['id']}"):
                    delete_saved_location(CURRENT_KEY, r['id'])
                    st.rerun()

# ------------------------------------------------------------------------------
# TAB 5: KEY ÜRETECİ (Yalnızca Admin Görür)
# ------------------------------------------------------------------------------
if IS_ADMIN:
    with active_tabs[4]:
        st.markdown("<h4 style='color:#00f3ff;'>🔑 Admin Paneli - Key Üreteci</h4>", unsafe_allow_html=True)
        
        with st.form("key_add_form"):
            new_key_code = st.text_input("Yeni Key Adı / Kodu:", placeholder="Örn: VIP_USER_99 veya key_abc123")
            new_key_note = st.text_input("Not / Kullanıcı Adı (İsteğe Bağlı):", placeholder="Örn: Ahmet Bey için üretildi")
            submit_key = st.form_submit_button("➕ Yeni Key Oluştur")
            
            if submit_key:
                if new_key_code.strip():
                    res = add_access_key(new_key_code.strip(), new_key_note.strip())
                    if res:
                        st.success(f"✅ Key Başarıyla Üretildi: `{new_key_code.strip()}`")
                        st.rerun()
                    else:
                        st.error("❌ Bu Key ismi zaten mevcut!")
                else:
                    st.warning("Lütfen bir Key kodu girin.")
        
        st.markdown("---")
        st.subheader("📋 Kayıtlı Aktif Keyler")
        keys_df = get_all_access_keys()
        
        if keys_df.empty:
            st.info("Sistemde oluşturulmuş kayıtlı Key bulunmuyor.")
        else:
            for idx, r in keys_df.iterrows():
                col_k1, col_k2, col_k3 = st.columns([2, 3, 1])
                with col_k1:
                    st.code(r['access_key'], language=None)
                with col_k2:
                    st.write(f"**Not:** {r['note'] if r['note'] else '-'} | **Tarih:** {r['created_at']}")
                with col_k3:
                    if st.button("Sil", key=f"del_k_{r['access_key']}"):
                        delete_access_key(r['access_key'])
                        st.success("Key silindi.")
                        st.rerun()
