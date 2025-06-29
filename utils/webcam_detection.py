import streamlit as st
import cv2
import datetime
import os
from PIL import Image

# Impor dari utils (modul lain di folder yang sama)
from utils.model import predict_melon_disease, MODEL
from utils.database import save_detection

# Pustaka Tambahan untuk Webcam Real-time
# PERHATIAN: Baris impor ini sangat penting untuk kompatibilitas versi Python 3.12 dan streamlit-webrtc 0.63.3
try:
    from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
    WEBRTC_AVAILABLE = True
except ImportError as e:
    # Tangkap ImportError dan berikan pesan detail
    st.error(f"Error: Pustaka 'streamlit-webrtc' tidak dapat diimpor. Pastikan semua dependensinya terinstal. Detail: {e}")
    WEBRTC_AVAILABLE = False
except Exception as e:
    # Tangkap Exception umum jika ada masalah lain saat impor
    st.error(f"Error tak terduga saat memuat fitur webcam. Detail: {e}")
    WEBRTC_AVAILABLE = False


def handle_webcam_detection():
    """
    Menangani logika deteksi webcam real-time, termasuk tampilan stream,
    pemrosesan frame, dan penyimpanan snapshot otomatis.
    """
    st.header("Deteksi Penyakit Daun Melon Real-time")
    st.write("Arahkan kamera Anda ke daun melon untuk deteksi instan!")

    if not WEBRTC_AVAILABLE:
        st.error("Fitur webcam tidak tersedia. Silakan instal `streamlit-webrtc`.")
    elif MODEL is None:
        st.error("Model AI belum dimuat. Fitur webcam tidak dapat berfungsi tanpa model.")
    else:
        # Kelas VideoProcessor untuk Deteksi Real-time
        # Kelas ini akan memproses setiap frame video yang datang dari webcam
        class MelonDiseaseProcessor(VideoProcessorBase):
            def __init__(self):
                self.model = MODEL
                self.confidence_threshold = st.session_state.get('confidence_threshold', 0.5)
                # Inisialisasi info deteksi di session state untuk webcam
                if 'current_detection_info' not in st.session_state:
                    st.session_state['current_detection_info'] = None
                # Flag untuk mencegah penyimpanan otomatis berulang pada setiap frame live
                st.session_state['webcam_last_saved_detection'] = None 

            def recv(self, frame):
                img = frame.to_ndarray(format="bgr24") # Mengambil frame sebagai numpy array (BGR)
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) # Konversi ke RGB untuk model

                # Ambil nilai threshold terbaru dari session state di setiap frame
                self.confidence_threshold = st.session_state.get('confidence_threshold', 0.5)

                annotated_img, diseases, avg_confidence, keterangan = \
                    predict_melon_disease(img_rgb, self.confidence_threshold)
                
                # Simpan informasi deteksi terbaru ke session state
                st.session_state['current_detection_info'] = {
                    "diseases": diseases,
                    "avg_confidence": avg_confidence,
                    "keterangan": keterangan, 
                    "annotated_frame": cv2.cvtColor(annotated_img, cv2.COLOR_RGB2BGR) # Simpan dalam BGR untuk st.image jika perlu
                }
                st.session_state['last_detection_source'] = 'webcam_live' 
                
                # --- LOGIKA SIMPAN OTOMATIS WEBCAM (PERHATIAN!) ---
                # Ini adalah tempat di mana Anda bisa mengimplementasikan simpan otomatis.
                # Namun, SANGAT DISARANKAN untuk tidak menyimpan setiap frame.
                # Anda perlu logika yang jauh lebih canggih di sini, seperti:
                # - Simpan hanya jika deteksi berubah signifikan (misal: dari 'Sehat' jadi 'Penyakit').
                # - Simpan hanya setiap N detik (misal: 5 detik sekali).
                # - Batasi jumlah total simpan otomatis per sesi.

                # Contoh sangat sederhana (dan berpotensi sangat boros): simpan jika deteksi berubah
                # if st.session_state['webcam_last_saved_detection'] != st.session_state['current_detection_info']:
                #     # Lakukan proses penyimpanan di sini. Ini akan memicu I/O disk dan DB yang banyak.
                #     # Untuk demonstrasi, ini akan menyebabkan banyak entri riwayat.
                #     pass 
                # st.session_state['webcam_last_saved_detection'] = st.session_state['current_detection_info'] # Update flag

                return frame.from_ndarray(cv2.cvtColor(annotated_img, cv2.COLOR_RGB2BGR), format="bgr24")

        webrtc_ctx = webrtc_streamer(
            key="melon_webcam_detection",
            video_processor_factory=MelonDiseaseProcessor,
            media_stream_constraints={
                "video": {
                    "width": {"ideal": 1280},     # atau 1920 jika ingin Full HD
                    "height": {"ideal": 720},
                    "frameRate": {"ideal": 30}
                },
                "audio": False
            },
            async_processing=True,
        )


        # --- Kontrol dan Tampilan Info Real-time ---
        if webrtc_ctx.state.playing:
            st.success("Deteksi real-time aktif! Arahkan kamera Anda ke daun melon.")
            
            # Tampilkan info deteksi terbaru yang diupdate dari processor
            if st.session_state['current_detection_info']: 
                info = st.session_state['current_detection_info']
                st.markdown("---")
                st.subheader("Info Deteksi Real-time:")
                if "Daun Sehat" in info["diseases"]:
                    st.write(f"Status: ✅ Daun melon terlihat **Sehat** (Keyakinan: {info['avg_confidence']*100:.1f}%)")
                else:
                    st.write(f"Penyakit Terdeteksi: ❗ **{', '.join(info['diseases'])}**")
                
                if info['keterangan']: 
                    st.write(f"Keterangan: {info['keterangan']}")
            
            st.markdown("---")

        else: # Ketika webcam tidak playing, tampilkan instruksi untuk memulai
            st.session_state['current_detection_info'] = None 
            st.info("Klik tombol 'Mulai Deteksi Real-time' di atas untuk mengaktifkan kamera.")