import streamlit as st
import numpy as np
from PIL import Image
import cv2 # Digunakan untuk menggambar bounding box
from ultralytics import YOLO # Import pustaka YOLO dari Ultralytics

# --- Lokasi File Model YOLO ---
# Pastikan file 'best.pt' ada di folder utama proyek (sejajar dengan app.py)
MODEL_PATH = "best.pt" 

# --- Memuat Model YOLO ---
# Menggunakan @st.cache_resource agar model hanya dimuat sekali saat aplikasi dimulai.
@st.cache_resource
def load_yolo_model():
    """
    Memuat model YOLO dari file .pt.
    Jika gagal memuat, akan menampilkan pesan error di Streamlit.
    """
    try:
        model = YOLO(MODEL_PATH)
        # st.sidebar.success(f"Model YOLO '{MODEL_PATH}' berhasil dimuat!") # Komen ini agar tidak selalu muncul
        return model
    except Exception as e:
        st.error(f"Gagal memuat model YOLO dari '{MODEL_PATH}': {e}. Pastikan file model ada di direktori yang benar.")
        return None

MODEL = load_yolo_model() # Panggil fungsi untuk memuat model

def predict_melon_disease(image_array, confidence_threshold=0.25):
    """
    Melakukan prediksi deteksi penyakit pada gambar menggunakan model YOLO.
    Mengembalikan gambar yang sudah dianotasi (dengan kotak dan label),
    daftar penyakit yang terdeteksi, rata-rata keyakinan, dan keterangan.

    Args:
        image_array (numpy.array): Gambar input sebagai array NumPy (format RGB).
        confidence_threshold (float): Ambang batas keyakinan (0.0-1.0) untuk melaporkan deteksi.

    Returns:
        tuple: (annotated_image, diseases_found_list, avg_confidence_output, keterangan_text)
    """
    # Jika model gagal dimuat sebelumnya, kembalikan error
    if MODEL is None:
        return image_array, ["Error: Model tidak dimuat."], 0.0, "Model deteksi tidak tersedia. Silakan hubungi administrator."

    image_input = image_array 

    # Lakukan prediksi dengan ambang batas rendah untuk mendapatkan semua deteksi mentah dari YOLO
    results = MODEL(image_input, conf=0.01, verbose=False) 

    annotated_image = image_array.copy() 
    diseases_found_list = [] 
    detected_disease_names = set() 
    
    total_confidence_diseases = 0.0
    num_disease_detections = 0
    
    is_any_disease_detected = False 
    
    healthy_detection_info = None 

    for r in results:
        boxes = r.boxes 
        names = r.names 
        
        for box in boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0]) 
            conf = float(box.conf[0])             
            cls_id = int(box.cls[0])              
            label = names[cls_id]                 

            # --- Pemrosesan Deteksi ---
            if label == "Daun Sehat": # Gunakan nama kelas persis seperti di model Anda
                if conf >= confidence_threshold:
                    healthy_detection_info = {"score": conf, "box": [x1, y1, x2, y2]}
                continue 

            # Jika ini adalah kelas penyakit (bukan 'Daun Sehat') DAN memenuhi ambang batas pengguna
            if conf >= confidence_threshold:
                is_any_disease_detected = True 
                
                color = (0, 0, 255) # Merah untuk penyakit
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)
                text = f"{label}: {conf:.2f}"
                text_y_pos = max(15, y1 - 10)
                cv2.putText(annotated_image, text, (x1, text_y_pos), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                diseases_found_list.append(f"{label} ({conf*100:.1f}%)")
                detected_disease_names.add(label)
                total_confidence_diseases += conf
                num_disease_detections += 1
    
    # --- DEBUG: Tampilkan Nama Kelas yang Terdeteksi (SANGAT PENTING!) ---
    st.sidebar.markdown("---")
    st.sidebar.text("DEBUG: Nama Kelas Penyakit Terdeteksi (dari model):")
    if detected_disease_names:
        for d_name in detected_disease_names:
            st.sidebar.text(f"- '{d_name}'") # Tampilkan dengan tanda kutip untuk melihat spasi/karakter tersembunyi
    else:
        st.sidebar.text("- Tidak ada kelas penyakit terdeteksi di atas threshold.")
    st.sidebar.markdown("---")
    # --- AKHIR DEBUG ---

    # --- LOGIKA KETERANGAN DAN KEYAKINAN AKHIR ---
    keterangan_text = ""
    avg_confidence_output = 0.0

    if is_any_disease_detected: 
        avg_confidence_output = total_confidence_diseases / num_disease_detections if num_disease_detections > 0 else 0.0
        
        # --- PERHATIKAN BAGIAN INI ---
        # GANTI "Downy Mildew" dan "Virus Gemini" di bawah ini
        # dengan NAMA KELAS YANG PERSIS SAMA seperti yang Anda lihat di output DEBUG di sidebar!
        if "Downy_Mildew" in detected_disease_names: # <<< GANTI NAMA KELAS INI
            keterangan_text += "Untuk embun bulu, pastikan drainase yang baik dan pertimbangkan fungisida yang tepat. "
        if "Virus_Gemini" in detected_disease_names: # <<< GANTI NAMA KELAS INI
            keterangan_text += "Virus Gemini sulit diobati; fokus pada pengendalian vektor (kutu kebul) dan pemusnahan tanaman terinfeksi. "
        # Tambahkan kondisi untuk kelas penyakit lain jika ada di model Anda
        # if "Nama Penyakit Lain Anda" in detected_disease_names:
        #    keterangan_text += "Rekomendasi untuk penyakit lain. "
        
        if not keterangan_text: 
            keterangan_text = "Beberapa penyakit tidak terdeteksi. Mohon konsultasi dengan ahli pertanian."

    elif healthy_detection_info: 
        diseases_found_list = ["Daun Sehat"]
        keterangan_text = "" 
        avg_confidence_output = healthy_detection_info['score'] 

    else: 
        diseases_found_list = ["Penyakit Tidak Terdeteksi"]
        keterangan_text = "Tidak ada penyakit yang terdeteksi pada daun melon ini pada tingkat keyakinan yang ditentukan. Daun mungkin sehat atau penyakit belum dapat terdeteksi."
        avg_confidence_output = 0.0 

    return annotated_image, diseases_found_list, avg_confidence_output, keterangan_text