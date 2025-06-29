import streamlit as st
import os
from utils.auth import authenticate_user, register_user, hash_password
from utils.database import init_db, add_user_to_db, get_user_from_db

# Pastikan database terinisialisasi saat aplikasi dimulai
init_db()

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(layout="wide", page_title="Deteksi Penyakit Daun Melon")

# --- Injeksi CSS Kustom untuk Menyembunyikan Sidebar Bawaan ---

st.markdown("""
<style>
/* Menyembunyikan sidebar bawaan Streamlit di halaman login */
[data-testid="stSidebar"] {
    display: none !important;
}

/* Mengatur agar konten utama mengisi seluruh lebar halaman jika sidebar disembunyikan */
section[data-testid="stSidebar"] + div {
    margin-left: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# --- Inisialisasi Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'fullname' not in st.session_state:
    st.session_state['fullname'] = None

def show_login_page():
    # ... sisa kode show_login_page() tetap sama ...
    st.title("Selamat Datang di Sistem Deteksi Penyakit Daun Melon 🌿🍈")
    st.write("Silakan Login atau Daftar untuk melanjutkan.")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("Login")
        with st.form("login_form"):
            username = st.text_input("Nama Pengguna")
            password = st.text_input("Kata Sandi", type="password")
            login_button = st.form_submit_button("Login")

            if login_button:
                user_data_from_db = get_user_from_db(username)
                if user_data_from_db and user_data_from_db[2] == hash_password(password):
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.session_state['fullname'] = user_data_from_db[3]
                    st.success(f"Login berhasil! Selamat datang, {st.session_state['fullname']}!")
                    st.rerun()
                else:
                    st.error("Nama pengguna atau kata sandi salah.")
    
    with col2:
        st.header("Daftar Akun Baru")
        with st.form("register_form"):
            new_fullname = st.text_input("Nama Lengkap", key="reg_fullname")
            new_username = st.text_input("Nama Pengguna Baru", key="reg_username")
            new_email = st.text_input("Alamat Email", key="reg_email")
            new_password = st.text_input("Kata Sandi Baru", type="password", key="reg_password")
            confirm_password = st.text_input("Konfirmasi Kata Sandi", type="password", key="reg_confirm_password")
            register_button = st.form_submit_button("Daftar")

            if register_button:
                if not new_fullname or not new_username or not new_email or not new_password or not confirm_password:
                    st.error("Semua kolom harus diisi.")
                elif new_password != confirm_password:
                    st.error("Kata sandi dan konfirmasi kata sandi tidak cocok.")
                else:
                    if add_user_to_db(new_username, hash_password(new_password), new_fullname, new_email):
                        st.success("Registrasi berhasil! Silakan Login.")
                    else:
                        st.error("Nama pengguna sudah ada. Silakan pilih yang lain.")

# --- Logika Routing Halaman ---
if st.session_state['logged_in']:
    st.switch_page("pages/main_app.py")
else:
    show_login_page()