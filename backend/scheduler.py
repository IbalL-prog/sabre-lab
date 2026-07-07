# Simpan di VS Code dengan nama: scheduler.py
import os
import sqlite3
from datetime import datetime, timedelta


def get_db_path():
    return os.getenv("DATABASE_PATH", "lab_reservation.db")

def inisialisasi_db():
    """Membuat database lokal dan tabel jika belum ada, serta mengisi data simulasi."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Buat tabel transaksi reservasi
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nim_nidn TEXT,
        id_lab TEXT,
        tanggal TEXT,
        jam_mulai TEXT,
        jam_selesai TEXT,
        nama_kegiatan TEXT
    )
    """)
    
    # Isi data dummy jadwal yang sudah terbooking untuk simulasi bentrok
    cursor.execute("SELECT COUNT(*) FROM reservations")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
        INSERT INTO reservations (nim_nidn, id_lab, tanggal, jam_mulai, jam_selesai, nama_kegiatan)
        VALUES (?, ?, ?, ?, ?, ?)
        """, [
            ("21101101", "Lab Komputer", "2026-06-27", "10:00", "12:00", "Praktikum Jaringan"),
            ("21101102", "Lab Komputer", "2026-06-27", "14:00", "16:00", "Workshop AI")
        ])
        conn.commit()
    conn.close()

def hitung_jam_selesai(jam_mulai_str, durasi_jam):
    """Menghitung jam selesai berdasarkan jam mulai dan durasi."""
    waktu_mulai = datetime.strptime(jam_mulai_str, "%H:%M")
    waktu_selesai = waktu_mulai + timedelta(hours=durasi_jam)
    return waktu_selesai.strftime("%H:%M")

def format_tanggal(tgl_str):
    """Mengubah format tanggal YYYY-MM-DD menjadi nama bulan bahasa Indonesia."""
    nama_bulan = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                  "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
    try:
        dt = datetime.strptime(tgl_str, "%Y-%m-%d")
        return f"{dt.day} {nama_bulan[dt.month - 1]} {dt.year}"
    except ValueError:
        return tgl_str

def cek_slot_kosong(id_lab, tanggal):
    """Mengembalikan daftar slot waktu yang tersedia untuk lab dan tanggal tertentu."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        "SELECT jam_mulai, jam_selesai FROM reservations WHERE LOWER(id_lab) = LOWER(?) AND tanggal = ?",
        (id_lab, tanggal)
    )
    jadwal_terisi = cursor.fetchall()
    conn.close()

    slot_tersedia = []
    for jam in range(8, 17):
        uji_mulai = f"{jam:02d}:00"
        uji_selesai = f"{jam + 1:02d}:00"
        tabrakan = False
        for mulai_b, selesai_b in jadwal_terisi:
            if uji_mulai < selesai_b and mulai_b < uji_selesai:
                tabrakan = True
                break
        if not tabrakan:
            slot_tersedia.append(f"{uji_mulai} - {uji_selesai}")
    return slot_tersedia

def cek_bentrok_dan_rekomendasi(nim_nidn, id_lab, tanggal, jam_mulai, durasi, nama_kegiatan):
    """
    Algoritma CSP untuk memeriksa tumpang tindih jadwal.
    Jika terjadi bentrok, sistem menscan slot waktu kosong pada jam kerja (08:00 - 17:00).
    """
    jam_selesai = hitung_jam_selesai(jam_mulai, durasi)
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    
    # Query mengambil semua jadwal aktif di lab & tanggal yang sama
    cursor.execute(
        "SELECT jam_mulai, jam_selesai FROM reservations WHERE LOWER(id_lab) = LOWER(?) AND tanggal = ?",
        (id_lab, tanggal)
    )
    jadwal_terisi = cursor.fetchall()
    
    # 1. Evaluasi Batasan CSP (Overlap Condition)
    bentrok = False
    for mulai_b, selesai_b in jadwal_terisi:
        # Rumus CSP Overlap: Mulai_A < Selesai_B DAN Mulai_B < Selesai_A
        if jam_mulai < selesai_b and mulai_b < jam_selesai:
            bentrok = True
            break
            
    if not bentrok:
        # Jika lolos validasi CSP, kunci slot dan simpan ke database
        cursor.execute("""
        INSERT INTO reservations (nim_nidn, id_lab, tanggal, jam_mulai, jam_selesai, nama_kegiatan)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (nim_nidn, id_lab, tanggal, jam_mulai, jam_selesai, nama_kegiatan))
        conn.commit()
        conn.close()
        tgl_format = format_tanggal(tanggal)
        return True, f"🎉 Selamat! Reservasi {id_lab} atas nama {nim_nidn} untuk kegiatan {nama_kegiatan} pada {tgl_format} pukul {jam_mulai} - {jam_selesai} telah berhasil."

    # 2. Solver CSP: Rekomendasikan slot alternatif jika terdeteksi konflik
    rekomendasi = []
    jam_buka, jam_tutup = 8, 17 # Jam operasional kampus
    
    for jam_uji in range(jam_buka, jam_tutup - durasi + 1):
        uji_mulai = f"{jam_uji:02d}:00"
        uji_selesai = hitung_jam_selesai(uji_mulai, durasi)
        
        tabrakan = False
        for mulai_b, selesai_b in jadwal_terisi:
            if uji_mulai < selesai_b and mulai_b < uji_selesai:
                tabrakan = True
                break
        if not tabrakan:
            rekomendasi.append(f"{uji_mulai}-{uji_selesai}")
            
    conn.close()
    tgl_format = format_tanggal(tanggal)
    opsi_str = "\n".join(f"{i+1}. {r}" for i, r in enumerate(rekomendasi[:3]))
    if opsi_str:
        return False, f"⚠️ Maaf, jadwal {id_lab} pada {tgl_format} pukul {jam_mulai} - {jam_selesai} sudah terbooking.\n\nBerikut jam alternatif yang tersedia:\n{opsi_str}\n\nSilakan pilih salah satu slot di atas."
    return False, f"❌ Maaf, jadwal {id_lab} pada {tgl_format} sudah penuh seharian. Silakan pilih tanggal lain."

def cari_booking(nim_nidn, id_lab, tanggal):
    """Mencari booking berdasarkan NIM/NIDN, lab, dan tanggal."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """SELECT id, nim_nidn, id_lab, tanggal, jam_mulai, jam_selesai, nama_kegiatan
           FROM reservations
           WHERE LOWER(nim_nidn)=LOWER(?) AND LOWER(id_lab)=LOWER(?) AND tanggal=?""",
        (nim_nidn, id_lab, tanggal)
    )
    hasil = cursor.fetchall()
    conn.close()
    return hasil

def batalkan_reservasi(booking_id):
    """Menghapus booking berdasarkan ID."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reservations WHERE id=?", (booking_id,))
    conn.commit()
    conn.close()

def lihat_jadwal_lab(id_lab, tanggal):
    """Mengembalikan daftar booking (NIM, jam, kegiatan) untuk lab & tanggal tertentu."""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute(
        """SELECT nim_nidn, jam_mulai, jam_selesai, nama_kegiatan
           FROM reservations
           WHERE LOWER(id_lab)=LOWER(?) AND tanggal=?
           ORDER BY jam_mulai""",
        (id_lab, tanggal)
    )
    hasil = cursor.fetchall()
    conn.close()
    return hasil


