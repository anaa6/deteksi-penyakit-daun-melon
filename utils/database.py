import sqlite3
import os
import json # Digunakan untuk menyimpan daftar penyakit sebagai string JSON di database

# Nama file database SQLite Anda
DB_NAME = 'melon_detector.db'

def init_db():
    """
    Menginisialisasi database SQLite dan membuat tabel `users` dan `detections`
    jika tabel-tabel tersebut belum ada. Fungsi ini akan dipanggil otomatis saat modul dimuat.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Tabel untuk menyimpan informasi pengguna
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            fullname TEXT,
            email TEXT
        )
    ''')

    # Tabel untuk menyimpan riwayat deteksi
    # image_path akan menyimpan lokasi file gambar di server
    # diseases akan menyimpan daftar penyakit dalam format JSON string
    c.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image_path TEXT,
            diseases TEXT,
            confidence REAL,
            recommendations TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def get_user_id(username):
    """
    Mengambil ID pengguna dari database berdasarkan username.
    Digunakan untuk mengaitkan deteksi dengan pengguna yang benar.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user_id = c.fetchone()
    conn.close()
    return user_id[0] if user_id else None

def add_user_to_db(username, password_hash, fullname, email):
    """
    Menambahkan pengguna baru ke tabel `users`.
    Mengembalikan True jika berhasil, False jika username sudah ada (IntegrityError).
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash, fullname, email) VALUES (?, ?, ?, ?)",
                  (username, password_hash, fullname, email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username sudah ada
    finally:
        conn.close()

def get_user_from_db(username):
    """
    Mengambil semua data pengguna dari database berdasarkan username.
    Berguna untuk proses login dan mengambil informasi profil.
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, username, password_hash, fullname, email FROM users WHERE username = ?", (username,))
    user_data = c.fetchone()
    conn.close()
    return user_data # Mengembalikan tuple: (id, username, password_hash, fullname, email)

def save_detection(username, image_path, diseases, confidence, recommendations):
    """
    Menyimpan hasil deteksi ke tabel `detections`.
    `diseases` akan disimpan sebagai JSON string karena bisa berisi daftar.
    """
    user_id = get_user_id(username)
    if user_id:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        diseases_json = json.dumps(diseases) # Mengubah daftar penyakit menjadi string JSON
        c.execute("INSERT INTO detections (user_id, image_path, diseases, confidence, recommendations) VALUES (?, ?, ?, ?, ?)",
                  (user_id, image_path, diseases_json, confidence, recommendations))
        conn.commit()
        conn.close()
        return True
    return False

def get_user_detections(username):
    """
    Mengambil semua riwayat deteksi untuk user tertentu.
    `diseases` yang tersimpan sebagai JSON string akan diuraikan kembali menjadi daftar.
    """
    user_id = get_user_id(username)
    if user_id:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT detection_date, image_path, diseases, confidence, recommendations FROM detections WHERE user_id = ? ORDER BY detection_date DESC", (user_id,))
        detections = c.fetchall()
        conn.close()
        
        parsed_detections = []
        for det in detections:
            date, path, diseases_json_str, conf, reco = det
            parsed_diseases = json.loads(diseases_json_str) if diseases_json_str else []
            parsed_detections.append((date, path, parsed_diseases, conf, reco))
        return parsed_detections
    return []

# Panggil fungsi inisialisasi database saat modul ini dimuat
init_db()