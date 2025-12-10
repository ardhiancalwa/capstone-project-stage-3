import streamlit as st
import pandas as pd
import numpy as np
import paho.mqtt.client as mqtt
import json
import joblib
import time
import uuid  # <--- IMPORT PENTING UNTUK FIX DUPLICATE KEY
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from collections import deque
from scipy import stats

# =====================================================
# 1. KONFIGURASI HALAMAN & CSS PREMIUM
# =====================================================
st.set_page_config(
    page_title="SmartAmbience Pro Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS dengan animasi dan glassmorphism
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* Main Background with gradient */
    .stApp {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Card Container with glassmorphism */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        margin-bottom: 20px;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    
    /* AI Status Banner dengan animasi */
    .ai-banner {
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        font-weight: 800;
        font-size: 28px;
        color: white;
        margin-bottom: 25px;
        border: 2px solid rgba(255,255,255,0.2);
        position: relative;
        overflow: hidden;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    
    .ai-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(
            45deg,
            rgba(255,255,255,0.1) 0%,
            rgba(255,255,255,0) 50%,
            rgba(255,255,255,0.1) 100%
        );
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0% { transform: translateX(-100%) translateY(-100%); }
        100% { transform: translateX(100%) translateY(100%); }
    }
    
    .bg-nyaman { 
        background: linear-gradient(135deg, #00b09b 0%, #96c93d 100%); 
        box-shadow: 0 8px 32px rgba(0,176,155,0.4);
    }
    .bg-panas { 
        background: linear-gradient(135deg, #ff512f 0%, #dd2476 100%); 
        box-shadow: 0 8px 32px rgba(255,81,47,0.4);
    }
    .bg-lembap { 
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
        box-shadow: 0 8px 32px rgba(79,172,254,0.4);
    }
    .bg-bahaya { 
        background: linear-gradient(135deg, #8E2DE2 0%, #4A00E0 100%);
        animation: pulse-glow 1.5s infinite;
        box-shadow: 0 8px 32px rgba(142,45,226,0.6);
    }
    
    @keyframes pulse-glow {
        0%, 100% { 
            transform: scale(1); 
            box-shadow: 0 8px 32px rgba(142,45,226,0.6);
        }
        50% { 
            transform: scale(1.02); 
            box-shadow: 0 12px 48px rgba(142,45,226,0.8);
        }
    }
    
    /* Stats Card */
    .stat-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        background: rgba(255, 255, 255, 0.08);
        transform: translateY(-3px);
    }
    
    .stat-value {
        font-size: 32px;
        font-weight: 700;
        color: #FFFFFF;
        margin: 10px 0;
    }
    
    .stat-label {
        font-size: 12px;
        color: #A0A0A0;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
    }
    
    .stat-change {
        font-size: 14px;
        font-weight: 600;
        margin-top: 5px;
    }
    
    .positive { color: #43e97b; }
    .negative { color: #ff512f; }
    
    /* Alert Badge */
    .alert-badge {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin: 5px;
        animation: fadeIn 0.5s ease;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .alert-warning {
        background: rgba(255, 193, 7, 0.2);
        color: #ffc107;
        border: 1px solid #ffc107;
    }
    
    .alert-danger {
        background: rgba(220, 53, 69, 0.2);
        color: #dc3545;
        border: 1px solid #dc3545;
    }
    
    .alert-success {
        background: rgba(40, 167, 69, 0.2);
        color: #28a745;
        border: 1px solid #28a745;
    }
    
    /* Connection Status */
    .connection-badge {
        display: inline-flex;
        align-items: center;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        gap: 8px;
    }
    
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        animation: pulse-dot 2s infinite;
    }
    
    @keyframes pulse-dot {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .connected {
        background: rgba(40, 167, 69, 0.2);
        color: #28a745;
        border: 1px solid #28a745;
    }
    
    .disconnected {
        background: rgba(220, 53, 69, 0.2);
        color: #dc3545;
        border: 1px solid #dc3545;
    }
    
    /* Section Header */
    .section-header {
        font-size: 18px;
        font-weight: 700;
        color: #FFFFFF;
        margin: 20px 0 15px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }
    
    /* Trend indicator */
    .trend-indicator {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        font-size: 14px;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 12px;
        margin-left: 10px;
    }
    
    .trend-up {
        background: rgba(255, 81, 47, 0.2);
        color: #ff512f;
    }
    
    .trend-down {
        background: rgba(0, 242, 254, 0.2);
        color: #00f2fe;
    }
    
    .trend-stable {
        background: rgba(150, 201, 61, 0.2);
        color: #96c93d;
    }
</style>
""", unsafe_allow_html=True)

# =====================================================
# 2. KONFIGURASI SISTEM
# =====================================================
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "smartambience/sensor/data"
MQTT_CLIENT_ID = f"dashboard_pro_{int(time.time())}"
MAX_HISTORY = 100 

# Load Model
@st.cache_resource
def load_models():
    try:
        model = joblib.load('room_condition_model.pkl')
        encoder = joblib.load('room_condition_label_encoder.pkl')
        return model, encoder
    except:
        return None, None

model, label_encoder = load_models()

# =====================================================
# 3. HELPER FUNCTIONS
# =====================================================
def get_statistics(df, column):
    if df.empty: return {'mean': 0, 'min': 0, 'max': 0, 'std': 0, 'current': 0}
    return {
        'mean': df[column].mean(),
        'min': df[column].min(),
        'max': df[column].max(),
        'std': df[column].std(),
        'current': df[column].iloc[-1]
    }

def calculate_trend(data_series, window=5):
    if len(data_series) < window: return "stable", 0
    recent = data_series[-window:]
    slope, _, _, _, _ = stats.linregress(range(len(recent)), recent)
    if abs(slope) < 0.1: return "stable", slope
    return ("up" if slope > 0 else "down"), slope

def generate_alerts(current_data, stats_data):
    alerts = []
    if current_data['temp'] > 32: alerts.append(('danger', '🔥', 'Suhu Sangat Tinggi', f"Suhu mencapai {current_data['temp']:.1f}°C"))
    elif current_data['temp'] > 28: alerts.append(('warning', '🌡️', 'Suhu Tinggi', f"Suhu {current_data['temp']:.1f}°C melebihi zona nyaman"))
    elif current_data['temp'] < 18: alerts.append(('warning', '❄️', 'Suhu Rendah', f"Suhu {current_data['temp']:.1f}°C di bawah zona nyaman"))
    
    if current_data['hum'] > 70: alerts.append(('warning', '💧', 'Kelembapan Tinggi', f"Kelembapan {current_data['hum']:.1f}% dapat menyebabkan jamur"))
    elif current_data['hum'] < 30: alerts.append(('warning', '🏜️', 'Kelembapan Rendah', f"Kelembapan {current_data['hum']:.1f}% terlalu kering"))
    
    if current_data['light'] < 200 and current_data['motion'] == 1: alerts.append(('warning', '💡', 'Cahaya Kurang', 'Cahaya terlalu redup saat ada aktivitas'))
    elif current_data['light'] > 1500: alerts.append(('warning', '☀️', 'Cahaya Berlebih', 'Cahaya terlalu terang'))
    
    if current_data['cond'] == 'Potensi Tidak Aman': alerts.append(('danger', '⚠️', 'PERINGATAN BAHAYA', 'Kondisi ruangan tidak aman'))
    return alerts

def create_enhanced_gauge(value, title, min_val, max_val, unit, ranges, optimal_range=None):
    bar_color = "#43e97b"
    for r in ranges:
        if r['range'][0] <= value <= r['range'][1]:
            bar_color = r['color']
            break
    
    steps = [{'range': r['range'], 'color': r['color']} for r in ranges]
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number+delta",
        value = value,
        domain = {'x': [0, 1], 'y': [0, 1]},
        number = {'suffix': unit, 'font': {'size': 24, 'color': "white", 'family': 'Inter'}, 'valueformat': '.1f'},
        title = {'text': f"<b>{title}</b>", 'font': {'size': 14, 'color': "#A0A0A0", 'family': 'Inter'}},
        delta = {'reference': (max_val + min_val) / 2, 'increasing': {'color': "#ff512f"}, 'decreasing': {'color': "#00f2fe"}},
        gauge = {
            'axis': {'range': [min_val, max_val], 'tickwidth': 2, 'tickcolor': "rgba(255,255,255,0.3)", 'tickfont': {'color': 'white', 'size': 10}},
            'bar': {'color': bar_color, 'thickness': 0.3},
            'bgcolor': "rgba(255,255,255,0.05)",
            'borderwidth': 2,
            'bordercolor': "rgba(255,255,255,0.2)",
            'steps': steps,
            'threshold': {'line': {'color': "white", 'width': 3}, 'thickness': 0.8, 'value': value}
        }
    ))
    
    if optimal_range:
        fig.add_annotation(
            x=0.5, y=-0.15, text=f"Optimal: {optimal_range[0]}-{optimal_range[1]}{unit}", showarrow=False,
            font={'size': 11, 'color': '#43e97b', 'family': 'Inter'}, bgcolor='rgba(67, 233, 123, 0.1)',
            bordercolor='#43e97b', borderwidth=1, borderpad=4, xanchor='center'
        )
    
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Inter"}, margin=dict(l=10, r=10, t=60, b=50), height=320)
    return fig

def create_distribution_chart(df, column, title):
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df[column], nbinsx=20, marker=dict(color=df[column], colorscale='Viridis', line=dict(color='white', width=1)), name=title
    ))
    fig.update_layout(
        title=dict(text=f"<b>Distribusi {title}</b>", font={'size': 14, 'color': 'white'}),
        xaxis_title=title, yaxis_title="Frekuensi", height=250, margin=dict(l=40, r=20, t=40, b=40),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.05)', font={'color': 'white', 'family': 'Inter'}, showlegend=False
    )
    return fig

def create_correlation_heatmap(df):
    corr_data = df[['temp', 'hum', 'light']].corr()
    fig = go.Figure(data=go.Heatmap(
        z=corr_data.values, x=['Suhu', 'Kelembapan', 'Cahaya'], y=['Suhu', 'Kelembapan', 'Cahaya'],
        colorscale='RdBu', zmid=0, text=corr_data.values, texttemplate='%{text:.2f}', textfont={"size": 12}, colorbar=dict(title="Korelasi")
    ))
    fig.update_layout(
        title=dict(text="<b>Korelasi Antar Sensor</b>", font={'size': 14, 'color': 'white'}),
        height=280, margin=dict(l=40, r=40, t=40, b=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font={'color': 'white', 'family': 'Inter'}
    )
    return fig

# =====================================================
# 4. MQTT LOGIC (THREAD SAFE)
# =====================================================
if 'mqtt_client' not in st.session_state:
    st.session_state.mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=MQTT_CLIENT_ID)

if 'data_buffer' not in st.session_state:
    st.session_state.data_buffer = deque(maxlen=MAX_HISTORY)

if 'connection_status' not in st.session_state:
    st.session_state.connection_status = False

if 'last_update' not in st.session_state:
    st.session_state.last_update = None

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0: client.connected_flag = True
    else: client.connected_flag = False

def on_disconnect(client, userdata, rc, properties=None):
    client.connected_flag = False

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        
        # AI Prediction
        condition = "Menganalisis..."
        if model and label_encoder:
            try:
                features = np.array([[payload['temperature'], payload['humidity'], payload['light_raw'], payload['motion']]])
                idx = model.predict(features)[0]
                condition = label_encoder.inverse_transform([idx])[0]
            except:
                condition = "AI Error"

        # Simpan ke attribut client (THREAD SAFE)
        client.latest_data = {
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'datetime': datetime.now(),
            'temp': payload['temperature'],
            'hum': payload['humidity'],
            'light': payload['light_raw'],
            'motion': payload['motion'],
            'cond': condition
        }
        client.has_new_data = True
    except Exception as e:
        pass

client = st.session_state.mqtt_client
if not client.is_connected():
    client.latest_data = None
    client.has_new_data = False
    client.connected_flag = False
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.subscribe(MQTT_TOPIC)
        client.loop_start()
    except:
        st.error("❌ Gagal terhubung ke MQTT Broker")

# =====================================================
# 5. DASHBOARD HEADER
# =====================================================
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("""
        <h1 style='margin: 0; padding: 0;'>
            🌱 <span style='background: linear-gradient(90deg, #43e97b 0%, #38f9d7 100%); 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            font-weight: 800;'>SmartAmbience Pro</span>
        </h1>
        <p style='color: #A0A0A0; font-size: 14px; margin-top: 5px;'>
            Real-time Environmental Intelligence System
        </p>
    """, unsafe_allow_html=True)

with col_status:
    is_connected = getattr(client, 'connected_flag', False)
    if is_connected:
        st.markdown("<div class='connection-badge connected'><div class='status-dot' style='background: #28a745;'></div>CONNECTED</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='connection-badge disconnected'><div class='status-dot' style='background: #dc3545;'></div>DISCONNECTED</div>", unsafe_allow_html=True)
    
    if st.session_state.last_update:
        time_ago = (datetime.now() - st.session_state.last_update).total_seconds()
        st.caption(f"📡 Update: {int(time_ago)}s ago")

st.markdown("---")

# =====================================================
# 6. SIDEBAR CONTROLS
# =====================================================
with st.sidebar:
    st.markdown("### 🎮 Control Panel")
    auto_refresh = st.toggle("🔴 Live Monitoring", value=True)
    st.markdown("---")
    refresh_rate = st.slider("⚡ Refresh Rate (s)", 0.5, 5.0, 1.0, 0.5)
    st.markdown("---")
    st.markdown("### 📊 Display Options")
    show_gauges = st.checkbox("Show Gauges", value=True)
    show_charts = st.checkbox("Show Time Series", value=True)
    show_analytics = st.checkbox("Show Analytics", value=True)
    show_distribution = st.checkbox("Show Distribution", value=False)
    st.markdown("---")
    st.markdown("### ⚙️ Alert Thresholds")
    temp_high = st.number_input("Temp High (°C)", value=28.0)
    temp_low = st.number_input("Temp Low (°C)", value=18.0)
    hum_high = st.number_input("Humidity High (%)", value=70.0)
    hum_low = st.number_input("Humidity Low (%)", value=30.0)
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.data_buffer.clear()
            st.rerun()
    
    # Download Button Logic - Outside main loop (Safe from key error)
    if len(st.session_state.data_buffer) > 0:
        df_export = pd.DataFrame(list(st.session_state.data_buffer))
        with col2:
            st.download_button(
                label="📥 Export",
                data=df_export.to_csv(index=False),
                file_name=f"smartambience_log_{int(time.time())}.csv",
                mime="text/csv",
                use_container_width=True,
                key="sidebar_download_btn"  # Static Key - Safe here
            )
    
    st.markdown("---")
    with st.expander("ℹ️ System Info"):
        st.write(f"**Buffer Size**: {len(st.session_state.data_buffer)}/{MAX_HISTORY}")
        st.write(f"**MQTT Broker**: {MQTT_BROKER}")
        st.write(f"**Topic**: {MQTT_TOPIC}")
        if model: st.success("✅ AI Model Loaded")
        else: st.warning("⚠️ AI Model Not Found")

# =====================================================
# 7. MAIN DASHBOARD LOOP
# =====================================================
placeholder = st.empty()

while auto_refresh:
    if getattr(client, 'has_new_data', False):
        st.session_state.data_buffer.append(client.latest_data)
        st.session_state.last_update = datetime.now()
        client.has_new_data = False

    with placeholder.container():
        # UUID unik untuk setiap iterasi refresh chart agar tidak error duplicate ID
        uid = str(uuid.uuid4())
        
        if len(st.session_state.data_buffer) > 0:
            current = st.session_state.data_buffer[-1]
            df = pd.DataFrame(list(st.session_state.data_buffer))
            
            temp_stats = get_statistics(df, 'temp')
            hum_stats = get_statistics(df, 'hum')
            light_stats = get_statistics(df, 'light')
            
            temp_trend, temp_slope = calculate_trend(df['temp'].values)
            hum_trend, hum_slope = calculate_trend(df['hum'].values)
            light_trend, light_slope = calculate_trend(df['light'].values)
            
            alerts = generate_alerts(current, {'temp': temp_stats, 'hum': hum_stats, 'light': light_stats})
            
            # SECTION 1: BANNER
            status_map = {
                'Nyaman': ('bg-nyaman', '✨', 'Kondisi ruangan optimal'),
                'Panas': ('bg-panas', '🔥', 'Suhu ruangan tinggi'),
                'Lembap': ('bg-lembap', '💧', 'Kelembapan tinggi'),
                'Potensi Tidak Aman': ('bg-bahaya', '⚠️', 'Perhatian diperlukan!')
            }
            bg_class, icon, desc = status_map.get(current['cond'], ('', '', ''))
            
            col_banner, col_alerts = st.columns([2, 1])
            with col_banner:
                st.markdown(f"""
                    <div class='ai-banner {bg_class}'>
                        {icon} {current['cond'].upper()}
                        <div style='font-size: 14px; font-weight: 400; margin-top: 5px; letter-spacing: 1px;'>{desc}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col_alerts:
                st.markdown("<div class='section-header'>🚨 Alerts</div>", unsafe_allow_html=True)
                if alerts:
                    for alert_type, emoji, title, message in alerts:
                        st.markdown(f"<div class='alert-badge alert-{alert_type}'>{emoji} <strong>{title}</strong>: {message}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='alert-badge alert-success'>✅ Semua Parameter Normal</div>", unsafe_allow_html=True)
            
            # SECTION 2: STATS
            st.markdown("<div class='section-header'>📊 Quick Statistics</div>", unsafe_allow_html=True)
            col1, col2, col3, col4, col5 = st.columns(5)
            metrics = [
                (col1, "🌡️", temp_stats['mean'], "Avg Temp", "°C", temp_trend, "#ff512f"),
                (col2, "💧", hum_stats['mean'], "Avg Humidity", "%", hum_trend, "#00f2fe"),
                (col3, "💡", light_stats['mean'], "Avg Light", "lx", light_trend, "#fddb92"),
                (col4, "📈", temp_stats['max'], "Max Temp", "°C", None, "#43e97b"),
                (col5, "📉", temp_stats['min'], "Min Temp", "°C", None, "#4facfe"),
            ]
            for col, emoji, value, label, unit, trend, color in metrics:
                with col:
                    trend_html = ""
                    if trend:
                        trend_icons = {'up': '↗️', 'down': '↘️', 'stable': '→'}
                        trend_classes = {'up': 'trend-up', 'down': 'trend-down', 'stable': 'trend-stable'}
                        trend_html = f"<div class='trend-indicator {trend_classes[trend]}'>{trend_icons[trend]}</div>"
                    st.markdown(f"""<div class='stat-card'><div style='font-size: 24px;'>{emoji}</div><div class='stat-value' style='color: {color};'>{value:.1f}{unit}</div><div class='stat-label'>{label}</div>{trend_html}</div>""", unsafe_allow_html=True)
            
            # SECTION 3: GAUGES
            if show_gauges:
                st.markdown("<div class='section-header'>🎯 Real-time Sensors</div>", unsafe_allow_html=True)
                col1, col2, col3, col4 = st.columns([1, 1, 1, 0.8])
                with col1:
                    st.plotly_chart(create_enhanced_gauge(current['temp'], "TEMPERATURE", 0, 50, "°C", [{'range': [0, 18], 'color': "#4facfe"}, {'range': [18, 28], 'color': "#43e97b"}, {'range': [28, 50], 'color': "#ff512f"}], optimal_range=(20, 26)), use_container_width=True, key=f"g_temp_{uid}")
                with col2:
                    st.plotly_chart(create_enhanced_gauge(current['hum'], "HUMIDITY", 0, 100, "%", [{'range': [0, 30], 'color': "#f09819"}, {'range': [30, 70], 'color': "#43e97b"}, {'range': [70, 100], 'color': "#00f2fe"}], optimal_range=(40, 60)), use_container_width=True, key=f"g_hum_{uid}")
                with col3:
                    st.plotly_chart(create_enhanced_gauge(current['light'], "LIGHT INTENSITY", 0, 2000, "lx", [{'range': [0, 200], 'color': "#303030"}, {'range': [200, 800], 'color': "#fddb92"}, {'range': [800, 2000], 'color': "#fff1eb"}], optimal_range=(300, 750)), use_container_width=True, key=f"g_light_{uid}")
                with col4:
                    motion_status = "DETECTED" if current['motion'] == 1 else "NO MOTION"
                    motion_color = "#43e97b" if current['motion'] == 1 else "#555555"
                    motion_icon = "🏃" if current['motion'] == 1 else "💤"
                    recent_motion = df['motion'].tail(10).sum()
                    st.markdown(f"""<div style="background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border-radius: 20px; padding: 25px; text-align: center; height: 200px; display: flex; flex-direction: column; justify-content: center; border: 1px solid {motion_color};"><div style="font-size: 14px; color: #A0A0A0; margin-bottom: 10px; text-transform: uppercase; font-weight: 600;">MOTION SENSOR</div><div style="font-size: 48px; margin: 10px 0;">{motion_icon}</div><div style="font-size: 16px; font-weight: 700; color: {motion_color}; letter-spacing: 1px;">{motion_status}</div><div style="font-size: 12px; color: #A0A0A0; margin-top: 10px;">{recent_motion}/10 detections</div></div>""", unsafe_allow_html=True)

            # SECTION 4: CHARTS
            if show_charts:
                st.markdown("<div class='section-header'>📈 Environmental Dynamics</div>", unsafe_allow_html=True)
                tab1, tab2, tab3 = st.tabs(["🌡️ Temperature & Humidity", "💡 Light Intensity", "🔍 All Sensors"])
                with tab1:
                    fig_main = make_subplots(rows=2, cols=1, subplot_titles=('Temperature Over Time', 'Humidity Over Time'), vertical_spacing=0.12, row_heights=[0.5, 0.5])
                    fig_main.add_trace(go.Scatter(x=df['timestamp'], y=df['temp'], name="Temperature", mode='lines+markers', line=dict(color='#ff512f', width=3), fill='tozeroy', fillcolor='rgba(255, 81, 47, 0.2)'), row=1, col=1)
                    fig_main.add_trace(go.Scatter(x=df['timestamp'], y=df['hum'], name="Humidity", mode='lines+markers', line=dict(color='#00f2fe', width=3)), row=2, col=1)
                    fig_main.update_layout(height=550, margin=dict(l=50, r=20, t=50, b=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.03)', font={'color': 'white', 'family': 'Inter'}, showlegend=False)
                    st.plotly_chart(fig_main, use_container_width=True, key=f"chart_temp_hum_{uid}")
                with tab2:
                    fig_light = go.Figure(go.Bar(x=df['timestamp'], y=df['light'], marker=dict(color=df['light'], colorscale='Sunsetdark')))
                    fig_light.update_layout(title="Light Intensity Over Time", height=400, margin=dict(l=50, r=20, t=50, b=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.03)', font={'color': 'white', 'family': 'Inter'}, showlegend=False)
                    st.plotly_chart(fig_light, use_container_width=True, key=f"chart_light_{uid}")
                with tab3:
                    fig_all = go.Figure()
                    df_norm = df.copy()
                    df_norm['temp_norm'] = (df_norm['temp'] - df_norm['temp'].min()) / (df_norm['temp'].max() - df_norm['temp'].min() + 0.001) * 100
                    df_norm['hum_norm'] = df_norm['hum']
                    df_norm['light_norm'] = (df_norm['light'] - df_norm['light'].min()) / (df_norm['light'].max() - df_norm['light'].min() + 0.001) * 100
                    fig_all.add_trace(go.Scatter(x=df_norm['timestamp'], y=df_norm['temp_norm'], name='Temp (norm)', mode='lines', line=dict(color='#ff512f')))
                    fig_all.add_trace(go.Scatter(x=df_norm['timestamp'], y=df_norm['hum_norm'], name='Hum', mode='lines', line=dict(color='#00f2fe')))
                    fig_all.add_trace(go.Scatter(x=df_norm['timestamp'], y=df_norm['light_norm'], name='Light (norm)', mode='lines', line=dict(color='#fddb92')))
                    fig_all.update_layout(title="Normalized Comparison", height=400, margin=dict(l=50, r=20, t=50, b=40), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(255,255,255,0.03)', font={'color': 'white', 'family': 'Inter'}, legend=dict(orientation="h", y=1.02))
                    st.plotly_chart(fig_all, use_container_width=True, key=f"chart_all_{uid}")

            # SECTION 5 & 6 (Analytics & Distribution)
            if show_analytics and len(df) >= 10:
                st.markdown("<div class='section-header'>🔬 Advanced Analytics</div>", unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                with col1:
                    condition_counts = df['cond'].value_counts()
                    fig_pie = go.Figure(data=[go.Pie(labels=condition_counts.index, values=condition_counts.values, hole=0.4)])
                    fig_pie.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor='rgba(0,0,0,0)', font={'color': 'white'}, showlegend=True)
                    st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{uid}")
                with col2:
                    if len(df) >= 10: st.plotly_chart(create_correlation_heatmap(df), use_container_width=True, key=f"corr_{uid}")
                
                stats_data = {'Sensor': ['Temp', 'Hum', 'Light'], 'Mean': [f"{temp_stats['mean']:.1f}", f"{hum_stats['mean']:.1f}", f"{light_stats['mean']:.0f}"]}
                st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

            if show_distribution and len(df) >= 20:
                st.markdown("<div class='section-header'>📊 Distribution Analysis</div>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns(3)
                with col1: st.plotly_chart(create_distribution_chart(df, 'temp', 'Temperature'), use_container_width=True, key=f"d_temp_{uid}")
                with col2: st.plotly_chart(create_distribution_chart(df, 'hum', 'Humidity'), use_container_width=True, key=f"d_hum_{uid}")
                with col3: st.plotly_chart(create_distribution_chart(df, 'light', 'Light'), use_container_width=True, key=f"d_light_{uid}")

            # SECTION 7: DATA TABLE
            with st.expander("📋 Detailed Data Log", expanded=False):
                # Download button with UNIQUE KEY based on timestamp inside loop
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Dataset",
                    data=csv,
                    file_name=f"smartambience_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key=f"dl_expanded_{uid}"  # Key is unique per refresh
                )
                st.dataframe(df[['timestamp', 'cond', 'temp', 'hum', 'light', 'motion']].sort_index(ascending=False), use_container_width=True, height=400)

        else:
            st.markdown("<div style='text-align: center; padding: 100px;'><h2>📡 Waiting for ESP32...</h2><p>Make sure MQTT publisher is running.</p></div>", unsafe_allow_html=True)

    time.sleep(refresh_rate)

if not auto_refresh: st.info("🔴 Live monitoring stopped.")