import streamlit as st
import os
import datetime
import numpy as np
from PIL import Image
import cv2
import io 

st.set_page_config(layout="wide", page_title="Deteksi Daun Melon")

# --- Injeksi CSS Kustom (Perbaikan untuk Sidebar) ---
st.markdown("""
<style>
/* HANYA Menyembunyikan daftar navigasi bawaan Streamlit */
[data-testid="stSidebarNav"] { /* <-- UBAH SELEKTORNYA DI SINI */
    display: none !important;
}

/* Optional: Jika Anda ingin menyesuaikan margin agar konten utama mengisi penuh */
/* Ini biasanya diperlukan jika stSidebarNav itu membuat ruang kosong */
/* Coba tanpa ini dulu, dan jika ada ruang kosong di kiri, tambahkan ini */
/*
section[data-testid="stSidebar"] + div {
    margin-left: 0 !important;
}
*/

/* Ukuran font dan jarak baris di sidebar */
[data-testid="stSidebarContent"] h3,
[data-testid="stSidebarContent"] h4 {
    font-size: 1.8em !important;
    line-height: 1.2 !important;
    padding-top: 10px;
    padding-bottom: 5px;
}

[data-testid="stSidebarContent"] p,
[data-testid="stSidebarContent"] label.st-c1,
[data-testid="stSidebarContent"] .st-emotion-cache-1j00v0 { /* Selektor untuk teks tombol */
    font-size: 1.3em !important;
    line-height: 1.2 !important;
}

[data-testid="stSidebarContent"] {
    overflow-wrap: break-word;
    word-wrap: break-word;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <style>
    video {
        max-width: 600px !important;  /* maksimal lebar video */
        height: auto !important;      /* agar proporsional */
        border-radius: 10px;          /* sudut membulat */
        display: block;               /* Memastikan elemen video adalah blok */
        margin-left: auto;            /* Tengah video jika kolomnya lebih lebar */
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Impor Modul Utilitas ---
from utils.auth import logout_user
from utils.model import predict_melon_disease, MODEL
from utils.database import save_detection

# Impor WEBRTC_AVAILABLE dari utils.webcam_detection
from utils.webcam_detection import WEBRTC_AVAILABLE # <--- INI SUDAH ADA

# --- TAMBAHKAN IMPOR FUNGSI HANDLER INI ---
from utils.image_detection import handle_image_upload_detection
from utils.webcam_detection import handle_webcam_detection
# --- AKHIR TAMBAH IMPOR ---


# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(layout="wide", page_title="Deteksi Daun Melon")

# --- Verifikasi Login ---
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Anda belum login. Silakan login terlebih dahulu.")
    st.switch_page("app.py")

# --- Inisialisasi Session State (Penting untuk persistensi data antar-rerun) ---
if 'confidence_threshold' not in st.session_state:
    st.session_state['confidence_threshold'] = 0.5 
if 'current_image_bytes' not in st.session_state: 
    st.session_state['current_image_bytes'] = None
if 'current_image_name' not in st.session_state: 
    st.session_state['current_image_name'] = None
if 'last_detection_source' not in st.session_state: 
    st.session_state['last_detection_source'] = None
if 'detection_results_display' not in st.session_state: 
    st.session_state['detection_results_display'] = {
        "annotated_image": None, 
        "diseases": [], 
        "avg_confidence": 0.0, 
        "keterangan": "", 
        "original_image_name": None, 
        "threshold_used": -1.0 
    }
if 'current_detection_info' not in st.session_state: # Untuk webcam, diisi oleh processor
    st.session_state['current_detection_info'] = None


# --- Sidebar Navigasi & Kontrol ---
with st.sidebar:
    st.markdown("## 🌿🍈 **Navigasi Aplikasi**") 
    st.markdown(f"### **Halo, {st.session_state['fullname']}!** 👋") 
    st.markdown("---")

    st.markdown("#### **Pilih Sumber Deteksi**")
    detection_source_options = ["Gambar (Unggah File) 🖼️"]
    if WEBRTC_AVAILABLE: 
        detection_source_options.append("Webcam (Real-time) 🎥")

    st.radio(
        "Pilih salah satu",
        detection_source_options,
        key="detection_source_radio" 
    )
    st.markdown("---")

    st.markdown("#### **Pengaturan Deteksi**")
    confidence_threshold_percent = st.slider(
        "Minimum Keyakinan Deteksi",
        min_value=0,
        max_value=100,
        value=int(st.session_state['confidence_threshold'] * 100),
        step=5,
        format="%d%%",
        key="confidence_slider"
    )
    st.session_state['confidence_threshold'] = confidence_threshold_percent / 100.0
    st.markdown("---")

    st.markdown("#### **Menu Utama**")
    if st.button("Riwayat Deteksi Saya 📅", use_container_width=True):
        st.switch_page("pages/history.py")
    if st.button("Bantuan & FAQ ❓", use_container_width=True):
        st.info("Fitur Bantuan & FAQ akan hadir di sini!")
    st.markdown("---")

    st.markdown("#### **Akun Saya**")
    if st.button("Logout 🚪", use_container_width=True):
        logout_user()


# --- Bagian Utama Aplikasi yang Memanggil Fungsi Handler ---

st.title("Sistem Deteksi Penyakit Daun Melon") # Judul utama halaman

# Ambil nilai pilihan sumber deteksi dari session_state
# Ini penting karena st.radio berada di sidebar, namun digunakan di bagian utama script
current_detection_source = st.session_state.get('detection_source_radio', "Gambar (Unggah File) 🖼️")

# Panggil fungsi penanganan berdasarkan pilihan sumber deteksi
if current_detection_source == "Gambar (Unggah File) 🖼️":
    handle_image_upload_detection() # <--- Sekarang terdefinisi karena diimpor
elif current_detection_source == "Webcam (Real-time) 🎥":
    handle_webcam_detection() # <--- Sekarang terdefinisi karena diimpor