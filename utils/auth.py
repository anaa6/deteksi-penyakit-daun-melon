import streamlit as st
import hashlib # Digunakan untuk hashing password, untuk keamanan
from utils.database import add_user_to_db, get_user_from_db # Mengimpor fungsi dari modul database

def hash_password(password):
    """
    Mengubah password teks biasa menjadi hash SHA256.
    Ini penting untuk keamanan agar password tidak tersimpan dalam bentuk teks jelas.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    """
    Mengautentikasi pengguna berdasarkan username dan password yang diberikan.
    Memeriksa kredensial terhadap data pengguna di database.
    """
    user_data = get_user_from_db(username) # Mengambil data pengguna dari database
    
    # Memeriksa apakah user ada dan password hash cocok
    if user_data and user_data[2] == hash_password(password): # user_data[2] adalah kolom password_hash di DB
        st.session_state['logged_in'] = True  # Menandai user sebagai sudah login
        st.session_state['username'] = username # Menyimpan username di session state
        st.session_state['fullname'] = user_data[3] # Menyimpan nama lengkap di session state
        return True # Autentikasi berhasil
    
    st.session_state['logged_in'] = False # Menandai user sebagai belum login
    return False # Autentikasi gagal

def register_user(username, password, fullname, email):
    """
    Mendaftarkan pengguna baru ke database.
    Mengembalikan True jika pendaftaran berhasil, False jika username sudah ada.
    """
    hashed_password = hash_password(password)
    # Memanggil fungsi dari database.py untuk menambahkan user
    return add_user_to_db(username, hashed_password, fullname, email)

def logout_user():
    """
    Melakukan logout pengguna dari sesi.
    Meriset status login dan mengarahkan kembali ke halaman login.
    """
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['fullname'] = None
    st.rerun() # Memaksa Streamlit untuk me-refresh halaman dan kembali ke kondisi awal (login)