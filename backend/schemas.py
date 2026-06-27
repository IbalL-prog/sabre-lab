# Simpan di VS Code dengan nama: schemas.py
from pydantic import BaseModel, Field
from typing import Optional

class DataReservasi(BaseModel):
    """Skema data terstruktur hasil ekstraksi AI dari percakapan pengguna."""
    nim_nidn: Optional[str] = Field(None, description="NIM Mahasiswa atau NIDN Dosen, contoh: 21101140")
    id_lab: Optional[str] = Field(None, description="Nama atau ID lab yang ingin dipinjam, contoh: Lab Komputer, Lab Bahasa")
    tanggal: Optional[str] = Field(None, description="Tanggal format YYYY-MM-DD. Konversi kata relatif seperti 'besok' atau 'lusa'.")
    jam_mulai: Optional[str] = Field(None, description="Jam mulai peminjaman format HH:MM, contoh: 10:00")
    durasi: Optional[int] = Field(None, description="Durasi peminjaman dalam satuan angka jam, contoh: 2")
    nama_kegiatan: Optional[str] = Field(None, description="Tujuan penggunaan laboratorium, contoh: Ujian Praktikum")
