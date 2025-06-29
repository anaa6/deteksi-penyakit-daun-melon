import streamlit as st
import pandas as pd # For displaying data in a table format
import os # To check for image file existence
from PIL import Image # To display images
import json # To parse the diseases JSON string from the database

# --- Import Utility Modules ---
from utils.auth import logout_user # Function for logging out
from utils.database import get_user_detections # Function to retrieve user's detection history

# --- Streamlit Page Configuration ---
st.set_page_config(layout="wide", page_title="Riwayat Deteksi Melon")

# --- Injeksi CSS Kustom (Perbaikan untuk Sidebar) ---
st.markdown("""
<style>
/* HANYA Menyembunyikan daftar navigasi bawaan Streamlit */
[data-testid="stSidebarNav"] { /* <-- UBAH SELEKTORNYA DI SINI */
    display: none !important;
}

/* Optional: Jika Anda ingin menyesuaikan margin agar konten utama mengisi penuh */
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
[data-testid="stSidebarContent"] .st-emotion-cache-1j00v0 {
    font-size: 1.3em !important;
    line-height: 1.2 !important;
}

[data-testid="stSidebarContent"] {
    overflow-wrap: break-word;
    word-wrap: break-word;
}
</style>
""", unsafe_allow_html=True)

# --- Login Verification ---
# Redirect users to the login page if they try to access this page without logging in.
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Anda belum login. Silakan login terlebih dahulu.")
    st.switch_page("app.py")

# --- Sidebar Navigation (Consistent with main_app.py) ---
with st.sidebar:
    st.markdown("### 🌿🍈 **Navigasi Aplikasi**")
    st.write(f"**Halo, {st.session_state['fullname']}!** 👋")
    st.markdown("---")

    st.markdown("#### **Pilih Sumber Deteksi**")
    # This radio button is just for display consistency; it doesn't change the main content here.
    st.radio(
        "Pilih salah satu",
        ("Gambar (Unggah File) 🖼️", "Webcam (Real-time) 🎥"),
        index=0, # Default to 'Gambar (Unggah File)'
        key="detection_source_history_radio", # Unique key for this page's radio button
        disabled=True # Disable interaction as this page doesn't perform new detections
    )
    st.markdown("---")

    st.markdown("#### **Pengaturan Deteksi**")
    # Display the confidence threshold from session state (disabled for editing here).
    st.slider(
        "Minimum Keyakinan Deteksi",
        min_value=0,
        max_value=100,
        value=int(st.session_state.get('confidence_threshold', 0.5) * 100),
        step=5,
        format="%d%%",
        key="confidence_slider_history", # Unique key
        disabled=True # Disable interaction here
    )
    st.markdown("---")

    st.markdown("#### **Menu Utama**")
    # Button to navigate back to the main detection page
    if st.button("Deteksi Baru 🌿", use_container_width=True):
        st.switch_page("pages/main_app.py")
    if st.button("Bantuan & FAQ ❓", use_container_width=True):
        st.info("Fitur Bantuan & FAQ akan hadir di sini!") # Placeholder
    st.markdown("---")

    st.markdown("#### **Akun Saya**")
    # Logout button
    if st.button("Logout 🚪", use_container_width=True):
        logout_user()


### **Area Konten Utama: Riwayat Deteksi**

st.title("Riwayat Deteksi Penyakit Anda")
st.write("Berikut adalah daftar deteksi penyakit daun melon yang pernah Anda lakukan.")

# Retrieve detection history for the current user
user_detections = get_user_detections(st.session_state['username'])

if user_detections:
    # Prepare data for DataFrame display
    df_data = []
    for det in user_detections:
        detection_date, image_path, diseases_list, confidence, recommendations = det
        df_data.append({
            "Tanggal Deteksi": detection_date,
            "Gambar_Path": image_path, # Keep path for internal use, don't display directly
            "Penyakit Terdeteksi": ", ".join(diseases_list) if isinstance(diseases_list, list) else diseases_list,
            "Keyakinan Rata-rata": f"{confidence*100:.1f}%",
            "Rekomendasi": recommendations
        })
    
    df = pd.DataFrame(df_data)
    
    # Display the table without the 'Gambar_Path' column initially
    st.dataframe(df.drop(columns=["Gambar_Path"]), use_container_width=True)

    st.subheader("Detail Gambar Riwayat")
    
    # Allow user to select an image from their history to view details
    image_paths_for_selection = df["Gambar_Path"].tolist()
    if image_paths_for_selection:
        selected_image_path = st.selectbox("Pilih gambar dari riwayat untuk melihat detailnya:", image_paths_for_selection)
        
        if selected_image_path:
            try:
                # Display the selected image
                st.image(selected_image_path, caption=f"Gambar: {os.path.basename(selected_image_path)}", use_column_width=True)
                
                # Find the corresponding detection details
                selected_detection = df[df["Gambar_Path"] == selected_image_path].iloc[0]
                
                # Display details from the selected detection
                st.write(f"**Tanggal Deteksi:** {selected_detection['Tanggal Deteksi']}")
                st.write(f"**Penyakit Terdeteksi:** {selected_detection['Penyakit Terdeteksi']}")
                st.write(f"**Keyakinan Rata-rata:** {selected_detection['Keyakinan Rata-rata']}")

                # --- BAGIAN INI DIMODIFIKASI ---
                if selected_detection['Rekomendasi']: # Kolom ini sekarang berisi 'keterangan_text'
                    st.info(f"**Keterangan:** {selected_detection['Rekomendasi']}") # Ubah label
                # --- AKHIR MODIFIKASI ---

            except FileNotFoundError:
                st.error("Gambar tidak ditemukan. Mungkin telah dihapus dari server.")
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memuat detail gambar: {e}")
    else:
        st.write("Tidak ada gambar yang dapat dipilih untuk detail.")

else:
    st.info("Anda belum memiliki riwayat deteksi. Mulai deteksi baru sekarang dari halaman utama!")