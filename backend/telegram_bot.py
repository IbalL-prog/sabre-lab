# Simpan di VS Code dengan nama: telegram_bot.py
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agent import jalankan_agen_reservasi

# PASTE TOKEN DARI BOTFATHER DI SINI
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Memori percakapan sementara di RAM untuk menyimpan riwayat chat per user ID
user_memories = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi pembuka saat pengguna mengetik /start di Telegram."""
    user_id = update.effective_user.id
    user_memories[user_id] = [] # Reset riwayat chat untuk sesi baru
    
    pesan_sambut = (
        "🤖 Halo! Saya Asisten Virtual Reservasi Lab.\n\n"
        "Untuk melakukan peminjaman, mohon berikan informasi berikut:\n"
        "1. NIM atau NIDN Anda\n"
        "2. Nama Laboratorium\n"
        "3. Tanggal Peminjaman\n"
        "4. Jam Mulai\n"
        "5. Durasi (berapa jam)\n"
        "6. Nama Kegiatan / Tujuan\n\n"
        "Contoh: 'Saya Budi NIM 211011 mau pinjam Lab Komputer besok jam 10:00 selama 2 jam untuk Praktikum Jaringan'"
    )
    await update.message.reply_text(pesan_sambut)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fungsi untuk menangani setiap pesan teks yang dikirim pengguna."""
    try:
        if not update.message:
            return
        user_id = update.effective_user.id
        user_text = update.message.text
        print(f"[LOG] Pesan dari {user_id}: {user_text}")
        
        # Inisialisasi memori jika pengguna baru pertama kali chat
        if user_id not in user_memories:
            user_memories[user_id] = []
            
        # Kirim teks ke backend Agen AI untuk diproses (Ekstraksi -> CSP Validasi)
        jawaban_ai = jalankan_agen_reservasi(user_text, riwayat_chat=user_memories[user_id])
        print(f"[LOG] Balasan: {jawaban_ai}")
        
        # Simpan percakapan ke dalam memori agar AI ingat konteks di chat berikutnya (Slot Filling)
        from langchain_core.messages import HumanMessage, AIMessage
        user_memories[user_id].append(HumanMessage(content=user_text))
        user_memories[user_id].append(AIMessage(content=jawaban_ai))
        
        # Batasi memori agar tidak terlalu panjang (maksimal 10 history terakhir)
        if len(user_memories[user_id]) > 10:
            user_memories[user_id] = user_memories[user_id][-10:]

        # Kirim balik jawaban akhir ke aplikasi Telegram pengguna
        await update.message.reply_text(jawaban_ai, parse_mode="Markdown")
    except Exception as e:
        print(f"[ERROR] handle_message: {e}")
        if update.message:
            await update.message.reply_text(f"Maaf, terjadi kesalahan: {e}")

def main():
    """Menjalankan bot Telegram."""
    print("🚀 Bot backend sedang berjalan... Tekan Ctrl+C untuk mematikan.")
    
    # Membangun aplikasi bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Mendaftarkan perintah /start dan pesan teks biasa
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Mulai mendengarkan chat masuk (metode Polling, tidak butuh Ngrok)
    application.run_polling()

if __name__ == '__main__':
    main()
