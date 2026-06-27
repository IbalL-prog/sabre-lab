import uuid
from datetime import datetime
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from agent import jalankan_agen_reservasi
from scheduler import lihat_jadwal_lab, cek_slot_kosong

app = FastAPI(title="SABRELab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.post("/api/chat")
async def chat(req: ChatRequest):
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
async def lab_detail(lab_name: str, tanggal: str | None = Query(None)):
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
async def daftar_lab():
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
