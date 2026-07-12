# services/whatsapp_notification.py
import requests
import threading

def get_parent_advice(emotion):
    """
    Kamus rekomendasi masukan untuk orang tua berdasarkan mood siswa.
    """
    advice_map = {
        "Sad": (
            "- Luangkan waktu sejenak malam ini untuk mengobrol santai dari hati ke hati.\n"
            "- Validasi perasaannya dan tanyakan apakah ada hal di sekolah yang membuatnya lelah.\n"
            "- Hindari langsung menghakimi atau menceramahi; cukup jadilah pendengar yang baik."
        ),
        "Angry": (
            "- Berikan ruang (*space*) bagi putra/putri Anda untuk menenangkan diri terlebih dahulu.\n"
            "- Saat suasananya sudah mencair, ajak bicara dengan nada suara yang tenang.\n"
            "- Tanyakan secara lembut apa yang memicu rasa frustrasinya hari ini."
        ),
        "Fear": (
            "- Berikan apresiasi atas usahanya hari ini untuk menumbuhkan rasa percaya dirinya kembali.\n"
            "- Tanyakan apakah ada materi pelajaran atau tekanan tugas yang membuatnya merasa cemas.\n"
            "- Yakinkan dia bahwa merasa takut atau tidak tahu adalah bagian normal dari proses belajar."
        )
    }
    # Kembalikan saran yang sesuai, atau saran umum jika emosi tidak terdaftar
    return advice_map.get(emotion, "- Tetap jalin komunikasi yang hangat dengan putra/putri Anda sepulang sekolah.")

def send_whatsapp_fonnte(target_phone, student_name, emotion):
    """
    Fungsi internal untuk mengirim data ke API Gateway Fonnte dengan pesan dinamis.
    """
    url = "https://api.fonnte.com/send"
    
    # ⚠️ SILAKAN GANTI DENGAN TOKEN ASLI DARI DASHBOARD FONNTE KAMU
    TOKEN_FONNTE = "L4z8YiU6KU6s51PQTcw4" 
    
    # Ambil masukan/saran otomatis sesuai emosi
    parent_advice = get_parent_advice(emotion)
    
    # Menyusun template pesan notifikasi yang lebih hangat dan berisi masukan
    message = (
        f"🔔 *NOTIFIKASI MOODMONITOR*\n\n"
        f"Yth. Orang Tua/Wali dari *{student_name}*,\n\n"
        f"Sistem AI kami mendeteksi bahwa putra/putri Anda menunjukkan indikasi emosi *{emotion}* "
        f"secara konsisten selama sesi pembelajaran hari ini.\n\n"
        f"💡 *Saran/Masukan Mandiri untuk Orang Tua di Rumah:*\n"
        f"{parent_advice}\n\n"
        f"Notifikasi ini dikirim otomatis sebagai bentuk kerja sama antara institusi dan orang tua "
        f"demi menjaga kesejahteraan mental (*well-being*) siswa. Terima kasih atas perhatian Anda."
    )
    
    payload = {
        'target': target_phone,
        'message': message,
        'countryCode': '62',
    }
    
    headers = {
        'Authorization': TOKEN_FONNTE
    }
    
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=10)
        print(f"Fonnte Response: {response.text}")
    except Exception as e:
        print(f"Gagal mengirim WhatsApp via Fonnte: {e}")

def trigger_whatsapp_notification(target_phone, student_name, emotion):
    """
    Fungsi pembungkus (wrapper) menggunakan Threading (anti-freeze).
    """
    thread = threading.Thread(
        target=send_whatsapp_fonnte, 
        args=(target_phone, student_name, emotion)
    )
    thread.daemon = True
    thread.start()