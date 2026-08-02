import streamlit as st
import folium
from streamlit_folium import st_folium
import sqlite3
import requests
import numpy as np
import pandas as pd
import json
import time
from datetime import datetime
import math
import os

# ==============================================================================
# 1. SAYFA VE TEMA YAPILANDIRMASI (Mobil & Modern)
# ==============================================================================
st.set_page_config(
    page_title="Pusuya Doğru - Kuantum Keşif",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Modern Glassmorphism & Neon Kuantum CSS
st.markdown("""
<style>
    /* Derin Kuantum Teması Arka Planı */
    .stApp {
        background: linear-gradient(135deg, #070510 0%, #0f0a21 50%, #080312 100%);
        color: #e2e8f0;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Üst Başlık & Hero Alanı */
    .hero-container {
        text-align: center;
        padding: 1.2rem 0.8rem;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
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

    /* Mobil Ekranlar İçin Özel CSS Uyarlamaları */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 1.5rem;
        }
        .stButton > button {
            height: 54px !important;
            font-size: 1.05rem !important;
        }
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    /* Modern Kuantum Kartları */
    .quantum-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(0, 243, 255, 0.18);
        border-radius: 16px;
        padding: 16px;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        margin-bottom: 12px;
    }
    
    /* Mobil Uyumlu Büyük Dokunmatik Butonlar */
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
    
    .stButton > button:active {
        transform: translateY(1px);
    }

    /* Tab Menü Stilleri */
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

# ==============================================================================
# 2. VERİTABANI YÖNETİMİ (SQLite)
# ==============================================================================
DB_FILE = "quantum_discoveries.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS discoveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
    conn.commit()
    conn.close()

def save_discovery(lat, lon, anomaly_type, power, intent, notes, ai_interpretation):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute('''
        INSERT INTO discoveries (timestamp, lat, lon, anomaly_type, power, intent, notes, ai_interpretation)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (now, lat, lon, anomaly_type, power, intent, notes, ai_interpretation))
    conn.commit()
    conn.close()

def get_all_discoveries():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM discoveries ORDER BY id DESC", conn)
    conn.close()
    return df

def delete_discovery(entry_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM discoveries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()

# Veritabanını başlat
init_db()

# ==============================================================================
# 3. KUANTUM ENTROPİ & ANOMALİ MOTORU
# ==============================================================================
def get_quantum_random_numbers(count=100):
    """
    ANU (Australian National University) Kuantum Rastgele Sayı API'sine bağlanır.
    Bağlantı başarısız olursa yüksek entropili pseudo-kuantum hesaplamasına düşer.
    """
    url = f"https://qrng.anu.edu.au/API/jsonI.php?length={count}&type=hex16&size=1"
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                hex_list = data["data"]
                # Hex değerleri [0, 1] aralığında float sayılara çevir
                floats = [int(h, 16) / 65535.0 for h in hex_list]
                return np.array(floats)
    except Exception:
        pass
    
    # Fallback: Pseudo-Kuantum Entropisi
    return np.random.uniform(0, 1, count)

def generate_quantum_point(center_lat, center_lon, radius_km, mode="Attractor"):
    """
    Kuantum rastgele sayılar kullanarak Attractor, Void veya Blindspot üretir.
    """
    q_data = get_quantum_random_numbers(150)
    
    # Km'yi dereceye çevirme yaklaşık hesabı
    lat_deg_per_km = 1 / 111.0
    lon_deg_per_km = 1 / (111.0 * math.cos(math.radians(center_lat)))
    
    # Rastgele noktalar simüle et
    u = q_data[:50]
    v = q_data[50:100]
    weights = q_data[100:150]
    
    radii = radius_km * np.sqrt(u)
    angles = 2 * math.pi * v
    
    dx = radii * np.cos(angles) * lon_deg_per_km
    dy = radii * np.sin(angles) * lat_deg_per_km
    
    lats = center_lat + dy
    lons = center_lon + dx
    
    if mode == "Attractor":
        # En yoğun kümelenmiş noktayı seç (Kuantum Yoğunlaşması)
        idx = np.argmax(weights)
        target_lat = lats[idx]
        target_lon = lons[idx]
        power = round(float(np.max(weights) * 9.5 + 1.2), 2)
    elif mode == "Void":
        # En seyrek / düşük entropili bölge
        idx = np.argmin(weights)
        target_lat = lats[idx]
        target_lon = lons[idx]
        power = round(float((1 - np.min(weights)) * 8.5 + 1.0), 2)
    else:  # Blindspot
        # Tekil tam rastgele nokta
        idx = np.random.randint(0, len(lats))
        target_lat = lats[idx]
        target_lon = lons[idx]
        power = round(float(np.random.uniform(1.5, 6.0)), 2)
        
    return target_lat, target_lon, power

# ==============================================================================
# 4. GROQ AI SENKRONİSİTE VE NİYET REHBERİ
# ==============================================================================
def analyze_intent_with_groq(api_key, intent, anomaly_type, power, notes=""):
    """
    Groq LLM API kullanarak kuantum keşif senkronisite analizini yapar.
    """
    if not api_key or api_key.startswith("gsk_***"):
        return "⚠️ Lütfen Ayarlar sekmesinden geçerli bir Groq API anahtarı girin."
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "json"
    }
    
    prompt = f"""
    Sen 'Pusuya Doğru' adlı kuantum keşif ve senkronisite rehberisin. 
    Kullanıcı bir Kuantum Anomali Noktasına gitmek üzere bir niyet belirledi.

    - Kullanıcının Niyeti: "{intent}"
    - Anomali Tipi: {anomaly_type}
    - Kuantum Anomali Gücü: {power} / 10
    - Kullanıcının Ek Notları/Hissi: "{notes}"

    Lütfen bu keşif gezisi için mistik, psikolojik ve senkronisite odaklı derin bir yorum yap. 
    Kullanıcının orada neye dikkat etmesi gerektiğini, işaretleri (semboller, renkler, rastlantılar) ve zihinsel odak noktasını kısaca (3-4 paragraf) açıkla.
    """
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "Sen derin sembolizm, kuantum fiziği ve senkronisite konularında uzman gizemli ve bilge bir keşif rehberisin."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=10)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        else:
            return f"API Hatası ({res.status_code}): {res.text}"
    except Exception as e:
        return f"Bağlantı hatası oluştu: {str(e)}"

# ==============================================================================
# 5. SESSION STATE BAŞLATMA
# ==============================================================================
if 'user_lat' not in st.session_state:
    st.session_state.user_lat = 41.2867  # Varsayılan: Samsun
if 'user_lon' not in st.session_state:
    st.session_state.user_lon = 36.3300
if 'active_point' not in st.session_state:
    st.session_state.active_point = None
if 'groq_key' not in st.session_state:
    st.session_state.groq_key = ""

# ==============================================================================
# 6. ARAYÜZ (STORY & TABS)
# ==============================================================================

# Hero Header
st.markdown("""
<div class="hero-container">
    <h1 class="hero-title">🔮 PUSUYA DOĞRU</h1>
    <p class="hero-subtitle">Kuantum Entropi Keşif & Anomali Tarayıcı</p>
</div>
""", unsafe_allow_html=True)

# Mobil Dostu Ana Tablar
tab_map, tab_ai, tab_history, tab_settings = st.tabs([
    "📍 Keşif Haritası", 
    "🤖 AI Niyet Analizi", 
    "📜 Keşif Günlüğü", 
    "⚙️ Ayarlar"
])

# ------------------------------------------------------------------------------
# TAB 1: KEŞİF HARİTASI VE KONTROLLER
# ------------------------------------------------------------------------------
with tab_map:
    
    # Hızlı Ayar Paneli
    with st.expander("🎯 Kuantum Parametreleri", expanded=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            anomaly_type = st.radio(
                "Anomali Türü:",
                ["Attractor (Yoğunluk)", "Void (Boşluk)", "Blindspot (Kör Nokta)"],
                index=0
            )
        with col_m2:
            search_radius = st.slider("Arama Yarıçapı (km):", min_value=1.0, max_value=15.0, value=3.0, step=0.5)
            user_intent_input = st.text_input("Niyetiniz / Odak Noktanız:", placeholder="Örn: Huzur, Bir işaret, Yeni bir kapı...")

    # ANA AKSİYON BUTONU
    if st.button("🌌 KUANTUM ANOMALİSİ ÜRET", use_container_width=True):
        with st.spinner("Kuantum entropi havuzuna bağlanılıyor..."):
            mode_clean = anomaly_type.split()[0]
            lat, lon, power = generate_quantum_point(
                st.session_state.user_lat, 
                st.session_state.user_lon, 
                search_radius, 
                mode=mode_clean
            )
            
            st.session_state.active_point = {
                "lat": lat,
                "lon": lon,
                "power": power,
                "type": mode_clean,
                "intent": user_intent_input if user_intent_input else "Belirtilmedi",
                "radius": search_radius
            }
            st.toast("✨ Yeni Kuantum Koordinat Tespiti Yapıldı!", icon="🎯")

    # HARİTA GÖRÜNÜMÜ
    st.markdown("<h4 style='color:#00f3ff; margin-top:10px;'>🗺️ Canlı Kuantum Sahası</h4>", unsafe_allow_html=True)
    
    m = folium.Map(
        location=[st.session_state.user_lat, st.session_state.user_lon],
        zoom_start=13,
        tiles="CartoDB dark_matter"
    )
    
    # Kullanıcı Konum İşaretçisi
    folium.Marker(
        [st.session_state.user_lat, st.session_state.user_lon],
        popup="Mevcut Konumunuz",
        icon=folium.Icon(color="blue", icon="user", prefix="fa")
    ).add_to(m)
    
    # Aktif Nokta Varsa Haritaya Ekle
    if st.session_state.active_point:
        apt = st.session_state.active_point
        
        # Etki Yarıçapı Dairesi
        folium.Circle(
            radius=180,
            location=[apt["lat"], apt["lon"]],
            color="#00f3ff",
            fill=True,
            fill_color="#9d4edd",
            fill_opacity=0.45
        ).add_to(m)
        
        # Hedef Marker
        folium.Marker(
            [apt["lat"], apt["lon"]],
            popup=f"Güç: {apt['power']} | Tip: {apt['type']}",
            icon=folium.Icon(color="red", icon="bullseye", prefix="fa")
        ).add_to(m)

    st_folium(m, width="100%", height=360, returned_objects=[])

    # AKTİF NOKTA DETAYLARI VE NAVİGASYON KARTI
    if st.session_state.active_point:
        apt = st.session_state.active_point
        st.markdown(f"""
        <div class="quantum-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #00f3ff; font-weight: bold; font-size:1.1rem;">⚡ {apt['type'].upper()} ANOMALİSİ</span>
                <span style="background: rgba(157, 78, 221, 0.3); padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; border: 1px solid #9d4edd; color:#e2e8f0;">Güç: {apt['power']}</span>
            </div>
            <p style="margin: 10px 0 5px 0; font-size: 0.9rem; color: #cbd5e1;">
                <b>Koordinatlar:</b> {apt['lat']:.5f}, {apt['lon']:.5f}<br>
                <b>Belirlenen Niyet:</b> {apt['intent']}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={apt['lat']},{apt['lon']}"
        st.markdown(f'''
            <a href="{gmaps_url}" target="_blank" style="text-decoration: none;">
                <button style="
                    background: linear-gradient(90deg, #10b981, #059669);
                    color: white;
                    width: 100%;
                    border-radius: 12px;
                    padding: 12px;
                    border: none;
                    font-weight: bold;
                    margin-bottom: 15px;
                    cursor: pointer;">
                    🧭 Google Maps ile Rotayı Başlat
                </button>
            </a>
        ''', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: AI NİYET ANALİZİ & YAPAY ZEKA REHBERİ
# ------------------------------------------------------------------------------
with tab_ai:
    st.markdown("<h4 style='color:#9d4edd;'>🤖 AI Kuantum Rehberi</h4>", unsafe_allow_html=True)
    
    if not st.session_state.active_point:
        st.info("ℹ️ Henüz aktif bir kuantum noktası üretmediniz. Lütfen önce 'Keşif Haritası' sekmesinden bir nokta oluşturun.")
    else:
        apt = st.session_state.active_point
        st.write(f"**Aktif Hedef:** {apt['type']} (Güç: {apt['power']})")
        st.write(f"**Niyetiniz:** {apt['intent']}")
        
        user_notes = st.text_area("Bölgedeki gözlemleriniz / hisleriniz:", placeholder="Oraya vardığınızda gördüğünüz ilginç şeyleri veya hissettiklerinizi yazın...")
        
        if st.button("🔮 Niyeti & Senkronisiteyi Yorumla", use_container_width=True):
            with st.spinner("Groq AI kuantum senkronisitesini analiz ediyor..."):
                ai_res = analyze_intent_with_groq(
                    st.session_state.groq_key, 
                    apt['intent'], 
                    apt['type'], 
                    apt['power'], 
                    user_notes
                )
                st.session_state['last_ai_res'] = ai_res
        
        if 'last_ai_res' in st.session_state:
            st.markdown(f"""
            <div class="quantum-card" style="border-color: #9d4edd;">
                <h5 style="color: #00f3ff; margin-top:0;">✨ Groq AI Senkronisite Analizi</h5>
                <div style="font-size: 0.95rem; line-height: 1.6; color: #e2e8f0;">
                    {st.session_state['last_ai_res']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Günlüğe Kaydet Butonu
            if st.button("💾 Bu Keşfi Günlüğe Kaydet"):
                save_discovery(
                    apt['lat'], 
                    apt['lon'], 
                    apt['type'], 
                    apt['power'], 
                    apt['intent'], 
                    user_notes, 
                    st.session_state['last_ai_res']
                )
                st.success("Keşif veritabanına başarıyla kaydedildi!")

# ------------------------------------------------------------------------------
# TAB 3: KEŞİF GÜNLÜĞÜ (SQLite Verileri)
# ------------------------------------------------------------------------------
with tab_history:
    st.markdown("<h4 style='color:#00f3ff;'>📜 Keşif Günlüğü & Anılar</h4>", unsafe_allow_html=True)
    
    discoveries_df = get_all_discoveries()
    
    if discoveries_df.empty:
        st.info("Henüz kaydedilmiş bir keşif bulunmuyor.")
    else:
        for idx, row in discoveries_df.iterrows():
            with st.container():
                st.markdown(f"""
                <div class="quantum-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span style="color:#00f3ff; font-weight:bold;">{row['anomaly_type']} Noktası</span>
                        <small style="color:#94a3b8;">{row['timestamp']}</small>
                    </div>
                    <p style="margin:6px 0; font-size:0.88rem; color:#cbd5e1;">
                        <b>Niyet:</b> {row['intent']} | <b>Güç:</b> {row['power']}<br>
                        <b>Notlar:</b> {row['notes'] if row['notes'] else 'Not eklenmedi.'}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("AI Yorumunu Göster / Detaylar"):
                    st.write(row['ai_interpretation'] if row['ai_interpretation'] else "AI yorumu alınmadı.")
                    if st.button(f"🗑️ Kaydı Sil #{row['id']}", key=f"del_{row['id']}"):
                        delete_discovery(row['id'])
                        st.rerun()

# ------------------------------------------------------------------------------
# TAB 4: AYARLAR VE GÜVENLİK
# ------------------------------------------------------------------------------
with tab_settings:
    st.markdown("<h4 style='color:#ff007f;'>⚙️ Sistem ve Konum Ayarları</h4>", unsafe_allow_html=True)
    
    with st.container():
        # Groq Key
        groq_input = st.text_input("Groq API Key (Llama3 Entegrasyonu):", value=st.session_state.groq_key, type="password")
        if groq_input != st.session_state.groq_key:
            st.session_state.groq_key = groq_input
            st.success("API Key güncellendi.")
            
        st.divider()
        
        # Manuel Konum Ayarlama (GPS Simülasyonu)
        st.subheader("📍 Başlangıç Konumu Ayarla")
        c1, c2 = st.columns(2)
        with c1:
            new_lat = st.number_input("Enlem (Latitude):", value=st.session_state.user_lat, format="%.5f")
        with c2:
            new_lon = st.number_input("Boylam (Longitude):", value=st.session_state.user_lon, format="%.5f")
            
        if st.button("📍 Konumu Güncelle"):
            st.session_state.user_lat = new_lat
            st.session_state.user_lon = new_lon
            st.success("Konum başarıyla güncellendi!")