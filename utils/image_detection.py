import streamlit as st
import numpy as np
from PIL import Image
import io
import os
import datetime

from utils.model import predict_melon_disease, MODEL
from utils.database import save_detection


# Fungsi untuk memproses gambar dan menyimpan hasilnya ke session_state
def process_and_store_detection_results(image_bytes, image_name, source_type):
    """
    Melakukan deteksi pada gambar yang diberikan (dalam bentuk bytes) dan menyimpan hasilnya
    serta informasi gambar ke st.session_state['detection_results_display'].
    Ini adalah fungsi inti yang dipanggil untuk memicu pemrosesan gambar.
    """
    if MODEL is None:
        st.session_state['detection_results_display'] = {
            "annotated_image": None, "diseases": [], "avg_confidence": 0.0, 
            "keterangan": "Model AI belum dimuat. Mohon periksa kembali konfigurasi model Anda.",
            "original_image_name": image_name, "threshold_used": -1.0
        }
        st.error("Model AI belum dimuat. Fitur deteksi tidak berfungsi.")
        return

    st.session_state['current_image_bytes'] = image_bytes
    st.session_state['current_image_name'] = image_name
    st.session_state['last_detection_source'] = source_type

    image_pil = Image.open(io.BytesIO(image_bytes))
    img_array = np.array(image_pil.convert('RGB'))

    current_threshold = st.session_state.get('confidence_threshold', 0.5) 

    with st.spinner('Menganalisis gambar dan mendeteksi penyakit...'):
        annotated_img_array, diseases_output, avg_confidence_output, keterangan_output_text = \
            predict_melon_disease(img_array, current_threshold)
        
        st.session_state['detection_results_display'] = {
            "annotated_image": annotated_img_array,
            "diseases": diseases_output,
            "avg_confidence": avg_confidence_output,
            "keterangan": keterangan_output_text,
            "original_image_name": image_name,
            "threshold_used": current_threshold 
        }


# Fungsi untuk menampilkan UI hasil deteksi untuk mode unggah gambar
def display_detection_results_ui():
    """
    Menampilkan UI hasil deteksi dari st.session_state['detection_results_display'].
    Fungsi ini hanya bertanggung jawab pada tampilan, tidak memicu pemrosesan ulang.
    """
    if st.session_state.get('current_image_bytes') is None or \
       st.session_state.get('last_detection_source') != 'upload':
        if 'detection_results_display' in st.session_state:
            del st.session_state['detection_results_display']
        if 'current_image_bytes' in st.session_state:
            del st.session_state['current_image_bytes']
        if 'current_image_name' in st.session_state:
            del st.session_state['current_image_name']
        return 

    st.subheader("Gambar yang diunggah:")
    st.image(io.BytesIO(st.session_state['current_image_bytes']), 
             caption=st.session_state['current_image_name'], 
             use_container_width=True) # Gunakan use_container_width
    
    if st.session_state['detection_results_display']:
        display_results = st.session_state['detection_results_display']
        
        st.subheader("Hasil Deteksi:")
        st.image(display_results['annotated_image'], caption='Hasil Deteksi', use_container_width=True) # Gunakan use_container_width

        if "Daun Sehat" in display_results['diseases']:
            st.success(f"✅ Daun melon terlihat **Sehat** (Keyakinan: {display_results['avg_confidence']*100:.1f}%)")
        else:
            st.error("❗ **Penyakit Terdeteksi:**")
            for disease_info in display_results['diseases']:
                st.write(f"- {disease_info}")
            
            if display_results['keterangan']: 
                st.info(f"**Keterangan:** {display_results['keterangan']}")
        
        # Logika simpan otomatis dipindahkan ke handle_image_upload_detection


# Fungsi utama untuk menangani unggah gambar dan deteksi otomatis
def handle_image_upload_detection():
    """
    Menangani logika unggah gambar, memicu deteksi otomatis, dan update live slider.
    Juga mengelola penyimpanan otomatis ke database saat unggah file baru.
    """
    st.header("Deteksi Penyakit dari Gambar")
    st.write("Unggah gambar daun melon Anda untuk analisis.")

    uploaded_file = st.file_uploader("Pilih gambar dari perangkat Anda", type=['png', 'jpg', 'jpeg'], key="image_uploader_main")

    # Deteksi otomatis saat file baru diunggah atau beralih sumber
    if uploaded_file is not None:
        if st.session_state.get('current_image_name') != uploaded_file.name or \
           st.session_state.get('last_detection_source') != 'upload' or \
           st.session_state.get('current_image_bytes') is None:
            
            image_bytes = uploaded_file.read()
            process_and_store_detection_results(image_bytes, uploaded_file.name, 'upload')
            st.session_state['pending_auto_save_upload'] = True # Set flag di session_state
            st.rerun() 

    # Logika untuk memicu pemrosesan ulang (update live) saat slider digeser.
    if st.session_state.get('current_image_bytes') is not None and \
       st.session_state.get('last_detection_source') == 'upload':
        
        current_threshold = st.session_state.get('confidence_threshold', 0.5)
        display_threshold_used = st.session_state.get('detection_results_display', {}).get('threshold_used', -1.0)
        
        if abs(display_threshold_used - current_threshold) > 0.001:
            process_and_store_detection_results(
                st.session_state['current_image_bytes'], 
                st.session_state['current_image_name'], 
                'upload'
            )
            st.rerun() 
    
    display_detection_results_ui()

    # --- LOGIKA SIMPAN OTOMATIS UNTUK UNGGAH GAMBAR BARU ---
    # Simpan hanya jika ada permintaan simpan otomatis yang tertunda
    # DAN hasilnya sudah tersedia di session_state
    if st.session_state.get('pending_auto_save_upload', False) and st.session_state['detection_results_display']:
        display_results = st.session_state['detection_results_display']
        
        save_dir = "temp_images"
        os.makedirs(save_dir, exist_ok=True)
        unique_filename = f"{st.session_state['username']}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{st.session_state['current_image_name']}"
        image_path_to_save = os.path.join(save_dir, unique_filename)
        
        try:
            Image.open(io.BytesIO(st.session_state['current_image_bytes'])).save(image_path_to_save)

            save_detection(
                st.session_state['username'],
                image_path_to_save,
                display_results['diseases'],
                display_results['avg_confidence'],
                display_results['keterangan']
            )
            st.success("Hasil deteksi telah disimpan secara otomatis ke riwayat Anda!")
            st.session_state['pending_auto_save_upload'] = False # Reset flag setelah berhasil disimpan
        except Exception as e:
            st.error(f"Gagal menyimpan hasil deteksi ke riwayat: {e}")
            # Opsional: tambahkan st.session_state['pending_auto_save_upload'] = False
            # agar tidak mencoba menyimpan lagi jika ada error.
            st.session_state['pending_auto_save_upload'] = False