# Simpan di VS Code dengan nama: agent.py
import json
import os
import re
from datetime import datetime
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from schemas import DataReservasi
from scheduler import cek_bentrok_dan_rekomendasi, cek_slot_kosong, format_tanggal, cari_booking, batalkan_reservasi, lihat_jadwal_lab

# Menggunakan model pintar yang mendukung output terstruktur yang valid
llm = ChatOpenAI(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

KEYWORD_RESERVASI = ["lab", "booking", "pinjam", "reservasi", "nim", "nidn",
                     "laboratorium", "peminjaman", "kegiatan", "praktikum", "workshop",
                     "komputer", "hari ini", "besok", "lusa", "tanggal", "jam",
                     "mau", "saya", "ruang"]

KEYWORD_CEK_SLOT = ["kosong", "tersedia", "slot", "jadwal", "lihat", "available", "waktu", "lowong"]

KEYWORD_BATAL = ["batal", "cancel", "hapus", "batalkan", "pembatalan"]

KEYWORD_LIHAT_BOOKING = ["siapa", "tampilkan", "daftar booking", "jadwal hari ini", "daftar peminjam"]

PROMPT_OBROLAN = ChatPromptTemplate.from_messages([
    ("system", "Anda adalah asisten ramah untuk administrasi laboratorium kampus. Jawab pertanyaan pengguna dengan singkat dan ramah. Gunakan bahasa Indonesia."),
    ("human", "{input}")
])

PROMPT_RESERVASI_CHAT = ChatPromptTemplate.from_messages([
    ("system", """Anda adalah asisten ramah untuk reservasi laboratorium kampus.
Tugas Anda mengumpulkan data reservasi secara bertahap dan natural.

Hari ini: {tanggal_hari_ini}.

Data yang dibutuhkan:
1. nim_nidn: NIM/NIDN peminjam
2. id_lab: Nama laboratorium
3. tanggal: Tanggal pinjam (YYYY-MM-DD)
4. jam_mulai: Jam mulai (HH:MM)
5. durasi: Durasi dalam jam (angka)
6. nama_kegiatan: Tujuan penggunaan

Aturan:
- Tanyakan data yang masih kosong satu per satu dengan ramah
- Jangan tanyakan data yang sudah ada di history
- Jika semua data sudah lengkap, output JSON SAJA tanpa teks lain
- Contoh output JSON: {{"nim_nidn": "23050749", "id_lab": "Lab Komputer", "tanggal": "2026-06-27", "jam_mulai": "10:00", "durasi": 3, "nama_kegiatan": "Praktikum Jaringan"}}
- Jika masih ada data kurang, jangan output JSON, tanyakan dengan ramah"""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

PROMPT_EKSTRAK_SLOT = ChatPromptTemplate.from_messages([
    ("system", """Ekstrak nama lab dan tanggal dari pertanyaan pengguna.
Hari ini: {tanggal_hari_ini}.
Output JSON SAJA tanpa teks lain: {{"id_lab": "nama_lab_atau_null", "tanggal": "YYYY-MM-DD_atau_null"}}"""),
    ("human", "{input}")
])

PROMPT_BATAL = ChatPromptTemplate.from_messages([
    ("system", """Anda adalah asisten untuk pembatalan reservasi laboratorium.

Hari ini: {tanggal_hari_ini}.

Data yang dibutuhkan untuk mencari booking:
1. nim_nidn: NIM/NIDN peminjam
2. id_lab: Nama laboratorium
3. tanggal: Tanggal booking (YYYY-MM-DD)

Aturan:
- Jika ada data yang kurang, tanyakan dengan ramah
- Jika semua data sudah lengkap dan user meminta pembatalan (ucapkan "iya") setelah data booking ditampilkan, output JSON: {{"action": "eksekusi_batal", "nim_nidn": "...", "id_lab": "...", "tanggal": "..."}}
- Jika semua data sudah lengkap tapi user belum konfirmasi, output JSON: {{"action": "cari", "nim_nidn": "...", "id_lab": "...", "tanggal": "..."}}
- Jika user menolak atau mengatakan "tidak", jawab "Pembatalan dibatalkan."""),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

def coba_parse_json_dan_reservasi(konten):
    """Coba parse JSON dari konten dan jalankan reservasi jika semua data lengkap."""
    cocok = re.search(r'\{.*\}', konten, re.DOTALL)
    if not cocok:
        return None
    try:
        data = json.loads(cocok.group())
        if not isinstance(data, dict):
            return None
        if all(k in data for k in ["nim_nidn", "id_lab", "tanggal", "jam_mulai", "durasi", "nama_kegiatan"]):
            if all([data["nim_nidn"], data["id_lab"], data["tanggal"], data["jam_mulai"], data["durasi"], data["nama_kegiatan"]]):
                extracted = DataReservasi(**data)
                _, pesan = cek_bentrok_dan_rekomendasi(
                    nim_nidn=extracted.nim_nidn,
                    id_lab=extracted.id_lab,
                    tanggal=extracted.tanggal,
                    jam_mulai=extracted.jam_mulai,
                    durasi=extracted.durasi,
                    nama_kegiatan=extracted.nama_kegiatan
                )
                return pesan
    except (json.JSONDecodeError, Exception):
        pass
    return None

def jalankan_agen_reservasi(teks_user, riwayat_chat=[]):
    """Memproses pesan masuk dari antarmuka chat, mengekstrak JSON, dan memvalidasi logistik."""
    response = None
    teks_lower = teks_user.lower()
    tanggal_sekarang = datetime.now().strftime("%Y-%m-%d")
    max_retry = 2

    # CEK KONTEKS PEMBATALAN
    sedang_batal = any(kata in teks_lower for kata in KEYWORD_BATAL)
    if not sedang_batal:
        for msg in reversed(riwayat_chat[-6:]):
            if isinstance(msg, AIMessage):
                if "Yakin ingin dibatalkan" in msg.content or "Silakan sebutkan NIM/NIDN" in msg.content:
                    sedang_batal = True
                break

    if sedang_batal:
        for _ in range(max_retry):
            messages = PROMPT_BATAL.format_messages(
                tanggal_hari_ini=tanggal_sekarang,
                history=riwayat_chat,
                input=teks_user
            )
            response = llm.invoke(messages)
            konten = response.content.strip()

            cocok = re.search(r'\{.*\}', konten, re.DOTALL)
            if not cocok:
                return konten

            data = json.loads(cocok.group())
            action = data.get("action")

            if action == "cari":
                bookings = cari_booking(data["nim_nidn"], data["id_lab"], data["tanggal"])
                if not bookings:
                    return "Data booking tidak ditemukan. Silakan periksa kembali NIM/NIDN, Lab, dan Tanggal."
                daftar = "\n".join(
                    f"{b[0]}. {b[2]} | {b[3]} | {b[4]}-{b[5]} | {b[6]}"
                    for b in bookings
                )
                return f"Ditemukan booking atas nama **{data['nim_nidn']}**:\n{daftar}\n\nYakin ingin dibatalkan? (iya/tidak)"

            elif action == "eksekusi_batal":
                bookings = cari_booking(data["nim_nidn"], data["id_lab"], data["tanggal"])
                if not bookings:
                    return "Data booking tidak ditemukan."
                for b in bookings:
                    batalkan_reservasi(b[0])
                return f"✅ Booking **{data['id_lab']}** atas **{data['nim_nidn']}** pada **{format_tanggal(data['tanggal'])}** berhasil dibatalkan."

        if response:
            return response.content
        return "Maaf, ada kesalahan saat memproses pembatalan. Silakan coba lagi."

    # CEK LIHAT BOOKING
    if any(kata in teks_lower for kata in KEYWORD_LIHAT_BOOKING):
        msg = PROMPT_EKSTRAK_SLOT.format_messages(
            tanggal_hari_ini=tanggal_sekarang, input=teks_user
        )
        resp = llm.invoke(msg)
        cocok = re.search(r'\{.*\}', resp.content, re.DOTALL)
        if cocok:
            data = json.loads(cocok.group())
            id_lab = data.get("id_lab", "")
            tgl = data.get("tanggal", "") or tanggal_sekarang
            if not id_lab:
                return "Lab belum jelas. Tolong sebutkan nama laboratoriumnya."
            bookings = lihat_jadwal_lab(id_lab, tgl)
            tgl_fmt = format_tanggal(tgl)
            if not bookings:
                return f"Tidak ada booking di **{id_lab}** pada **{tgl_fmt}**."
            daftar_terisi = "\n".join(
                f"{i+1}. {b[1]}-{b[2]} | {b[0]} | {b[3]}"
                for i, b in enumerate(bookings)
            )
            tersedia = cek_slot_kosong(id_lab, tgl)
            if tersedia:
                slot_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(tersedia))
                return f"📋 **Jadwal {id_lab} - {tgl_fmt}**\n\nTerisi:\n{daftar_terisi}\n\nSlot kosong:\n{slot_str}"
            else:
                return f"📋 **Jadwal {id_lab} - {tgl_fmt}**\n\nTerisi:\n{daftar_terisi}\n\nMaaf, tidak ada slot kosong tersedia."
        if resp:
            return resp.content

    if not any(kata in teks_lower for kata in KEYWORD_RESERVASI):
        obrolan = PROMPT_OBROLAN.format_messages(input=teks_user)
        resp = llm.invoke(obrolan)
        return resp.content

    if any(kata in teks_lower for kata in KEYWORD_CEK_SLOT):
        msg = PROMPT_EKSTRAK_SLOT.format_messages(
            tanggal_hari_ini=tanggal_sekarang, input=teks_user
        )
        resp = llm.invoke(msg)
        cocok = re.search(r'\{.*\}', resp.content, re.DOTALL)
        if cocok:
            data = json.loads(cocok.group())
            id_lab = data.get("id_lab", "")
            tgl = data.get("tanggal", "") or tanggal_sekarang
            if not id_lab:
                return "Lab atau tanggal belum jelas. Tolong sebutkan nama lab dan tanggalnya."
            tersedia = cek_slot_kosong(id_lab, tgl)
            tgl_fmt = format_tanggal(tgl)
            if not tersedia:
                return f"Maaf, {id_lab} pada {tgl_fmt} sudah penuh seharian."
            slot_str = "\n".join(f"{i+1}. {s}" for i, s in enumerate(tersedia))
            return f"Berikut slot kosong di {id_lab} untuk {tgl_fmt}:\n{slot_str}"

    for _ in range(max_retry):
        messages = PROMPT_RESERVASI_CHAT.format_messages(
            tanggal_hari_ini=tanggal_sekarang,
            history=riwayat_chat,
            input=teks_user
        )
        response = llm.invoke(messages)
        konten = response.content.strip()

        isi_json = coba_parse_json_dan_reservasi(konten)
        if isi_json:
            return isi_json

        if not konten.startswith("{"):
            return konten

    if response:
        return response.content
    return "Maaf, ada kesalahan. Silakan coba lagi."
