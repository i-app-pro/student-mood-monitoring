# app.py
import streamlit as st
from database.db import init_db

# Inisialisasi database
init_db()

# Konfigurasi halaman global
st.set_page_config(
    page_title="MoodMonitor", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Memuat Google Material Icons agar icon bawaan Streamlit ter-render sempurna
st.markdown("""
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">
""", unsafe_allow_html=True)

# Global custom CSS untuk tampilan premium, perbaikan tombol, dan menu setting
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, .stApp, .stApp p, .stApp h1, .stApp h2, .stApp h3 {
        font-family: 'Outfit', 'Inter', sans-serif !important;
    }
    
    
    /* 1. Mengaktifkan kembali Toolbar Utama agar Menu Setting / Titik Tiga Kanan Atas Muncul */
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        z-index: 99999 !important;
        background-color: transparent !important;
        background: transparent !important;
        display: flex !important;
        visibility: visible !important;
    }

    /* 2. Mengubah Tombol Bawaan << (Saat Sidebar Terbuka) */
    [data-testid="stSidebarCollapseButton"] button {
        background-color: #1E3A8A !important;    /* Warna Biru Tua */
        color: #FFFFFF !important;               /* Panah Putih */
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        width: 38px !important;
        height: 38px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    /* 3. Mengubah Tombol Bawaan >> (Saat Sidebar Tertutup di Pojok Kiri Atas) */
    [data-testid="stHeader"] button[aria-label="Open sidebar"],
    div[data-testid="stHeader"] button:first-child {
        background-color: #1E3A8A !important;    /* Warna Biru Tua */
        color: #FFFFFF !important;               /* Panah Putih */
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        width: 40px !important;
        height: 40px !important;
        position: fixed !important;
        top: 12px !important;
        left: 15px !important;
        z-index: 999999 !important;
        display: inline-flex !important;
        visibility: visible !important;
    }

    /* Memaksa warna ikon di dalam kedua tombol (<< dan >>) menjadi putih bersih */
    [data-testid="stSidebarCollapseButton"] button svg,
    [data-testid="stHeader"] button[aria-label="Open sidebar"] svg,
    div[data-testid="stHeader"] button:first-child svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
        width: 20px !important;
        height: 20px !important;
    }

    /* Efek Hover untuk kedua tombol */
    [data-testid="stSidebarCollapseButton"] button:hover,
    [data-testid="stHeader"] button[aria-label="Open sidebar"]:hover,
    div[data-testid="stHeader"] button:first-child:hover {
        background-color: #3B82F6 !important;    /* Biru Terang saat di-hover */
        color: #FFFFFF !important;
        cursor: pointer !important;
    }

    /* Styling Area Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    
    [data-testid="stSidebarNav"] {
        background-color: transparent !important;
        padding-top: 10px !important;
        margin-bottom: 80px !important;
    }
    
    [data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a {
        color: #334155 !important;
        text-decoration: none !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a:hover {
        background-color: #F1F5F9 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a span {
        color: #334155 !important;
    }
    
    /* Link Navigasi Aktif */
    [data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a[aria-current="page"] {
        background-color: #EFF6FF !important;
        border-left: 4px solid #3B82F6 !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a[aria-current="page"] span {
        color: #1E3A8A !important;
        font-weight: 700 !important;
    }
    
    footer {visibility: hidden;}
    
    .stApp {
        background-color: #F8FAFC;
    }
    
    .sidebar-header {
        padding: 10px 10px 20px 10px;
        border-bottom: 1px solid #E2E8F0;
        margin-bottom: 15px;
    }
    .sidebar-footer {
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 220px;
        padding-top: 15px;
        border-top: 1px solid #E2E8F0;
        display: flex;
        align-items: center;
        gap: 12px;
        background-color: #F8FAFC;
        z-index: 999;
    }
    
    .avatar {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background-color: #3B82F6;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        font-size: 14px;
    }
    .profile-info {
        display: flex;
        flex-direction: column;
    }
    .profile-name {
        font-size: 13px;
        font-weight: 600;
        color: #1E293B;
    }
    .profile-role {
        font-size: 11px;
        color: #64748B;
    }
</style>
""", unsafe_allow_html=True)

# Custom header di bagian atas sidebar
st.sidebar.markdown("""
<div class="sidebar-header">
    <h1 style="font-size: 24px; color: #1E3A8A; margin-bottom: 0px; font-weight: 800; letter-spacing: -0.02em;">Admin Panel</h1>
    <p style="font-size: 12px; color: #64748B; margin-top: 0px; font-weight: 500;">Academic Supervisor</p>
</div>
""", unsafe_allow_html=True)

# Definisikan halaman navigasi
dashboard_page = st.Page("pages/dashboard.py", title="Dashboard", icon="📊")
detection_page = st.Page("pages/detection.py", title="Emotion Detection", icon="😊")
history_page = st.Page("pages/history.py", title="Student Records", icon="📜")

pg = st.navigation({
    "MoodMonitor": [dashboard_page, detection_page, history_page]
})

# Jalankan halaman yang terpilih
pg.run()

# Custom footer di bagian bawah sidebar
st.sidebar.markdown("""
<div class="sidebar-footer">
    <div class="avatar">SJ</div>
    <div class="profile-info">
        <span class="profile-name">Dr. Sarah Jenkins</span>
        <span class="profile-role">Academic Admin</span>
    </div>
</div>
""", unsafe_allow_html=True)