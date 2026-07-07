import os
import uuid
import threading
from datetime import datetime
from fastapi import FastAPI, Query, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter # pyright: ignore[reportMissingImports]
from slowapi.extension import _rate_limit_exceeded_handler # pyright: ignore[reportMissingImports]
from slowapi.util import get_remote_address # pyright: ignore[reportMissingImports]
from slowapi.errors import RateLimitExceeded # pyright: ignore[reportMissingImports]
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from agent import jalankan_agen_reservasi
from scheduler import inisialisasi_db, lihat_jadwal_lab, cek_slot_kosong, format_tanggal

app = FastAPI(title="SABRELab API")

# --- Rate Limiter ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
cors_origins = os.getenv("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins.split(",") if cors_origins != "*" else ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Auth ---
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")

def verify_token(authorization: str = Header(None)):
    if not API_AUTH_TOKEN:
        return
    if not authorization or authorization != f"Bearer {API_AUTH_TOKEN}":
        raise HTTPException(status_code=403, detail="Forbidden")

RATE_LIMIT = os.getenv("RATE_LIMIT", "30/minute")

sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.post("/api/chat")
@limiter.limit(RATE_LIMIT)
async def chat(request: Request, req: ChatRequest, authorization: str = Header(None)):
    verify_token(authorization)

    if not req.session_id or req.session_id not in sessions:
        session_id = str(uuid.uuid4())
        sessions[session_id] = []
    else:
        session_id = req.session_id

    memory = sessions[session_id]
    reply = jalankan_agen_reservasi(req.message, riwayat_chat=memory)

    memory.append(HumanMessage(content=req.message))
    memory.append(AIMessage(content=reply))

    if len(memory) > 10:
        memory = memory[-10:]

    sessions[session_id] = memory

    return ChatResponse(reply=reply, session_id=session_id)

@app.get("/api/lab/{lab_name}")
@limiter.limit(RATE_LIMIT)
async def lab_detail(request: Request, lab_name: str, tanggal: str | None = Query(None), authorization: str = Header(None)):
    verify_token(authorization)

    if not tanggal:
        tanggal = datetime.now().strftime("%Y-%m-%d")

    bookings = lihat_jadwal_lab(lab_name, tanggal)
    tersedia = cek_slot_kosong(lab_name, tanggal)
    tgl_fmt = format_tanggal(tanggal)

    return {
        "lab_name": lab_name,
        "tanggal": tanggal,
        "tanggal_format": tgl_fmt,
        "status": "Tersedia" if not bookings else ("Penuh" if not tersedia else "Terbooking"),
        "bookings": [
            {
                "nim_nidn": b[0],
                "jam_mulai": b[1],
                "jam_selesai": b[2],
                "nama_kegiatan": b[3]
            }
            for b in bookings
        ],
        "slot_tersedia": tersedia
    }

@app.get("/api/labs")
@limiter.limit(RATE_LIMIT)
async def daftar_lab(request: Request, authorization: str = Header(None)):
    verify_token(authorization)
    """Mengembalikan daftar lab dan statusnya hari ini."""
    labs = ["Lab Komputer 1", "Lab Komputer 2"]
    tanggal = datetime.now().strftime("%Y-%m-%d")
    hasil = []
    for lab in labs:
        bookings = lihat_jadwal_lab(lab, tanggal)
        tersedia = cek_slot_kosong(lab, tanggal)
        hasil.append({
            "id": lab,
            "status": "Tersedia" if not bookings else ("Penuh" if not tersedia else "Terbooking")
        })
    return hasil

@app.on_event("startup")
def startup():
    try:
        inisialisasi_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️ Gagal inisialisasi DB: {e}")

    try:
        from telegram_bot import start_bot
        t = threading.Thread(target=start_bot, daemon=True)
        t.start()
        print("✅ Telegram Bot thread started")
    except Exception as e:
        print(f"⚠️ Gagal start Telegram Bot: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
