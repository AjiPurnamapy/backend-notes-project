import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from backend.routers import notes, auth
from backend.database import engine
from backend.admin import setup_admin
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.limiter import limiter
from backend.admin import SECRET_KEY_ADMIN

# konfigurasi Logging, mengganti dari "print" menjadi "logging"
# mulai sekarang pakai logging.info bukan print
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Lifespan: jalan otomatis saat server nyala
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Server Sedang Menyala...")
    # create_db_table()      # perintah: "buat semua tabel yg di-import"
    logger.info("🛑 Server dimatikan.")
    yield 

app = FastAPI(
    title="Notes API Service",
    description="API sederhana untuk menyimpan catatan pribadi dengan fitur login & register",
    version="1.0.0",
    lifespan=lifespan
)

origin = [
    "http://127.0.0.1:5500", # live server VScode biasanya menggunakan port ini 
    "http://localhost:5500", # live server VScode biasanya menggunakan port ini 
    "http://localhost:3000", # react default port 
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY_ADMIN,
    max_age=3600, 
    https_only=False,
)

# pasang state limiter ke app
app.state.limiter = limiter
# pasang penanganan error (agar jika limit habis muncul pesan jelas)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# sambungkan jalur router ke app
app.include_router(auth.router)
app.include_router(notes.router)

# pasang admin panel
setup_admin(app, engine)

@app.get("/")
def read_root():
    logger.info("Ada yang akses endpoint root")
    return {"message": "Hello World"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # log error nya hanya bisa dilihat programer
    logger.error (f"FATAL ERROR TERJADI: {exc}")

    # response ke user
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "fail",
            "message": "terjadi kesalahan internal pada server. silahkan coba lagi nanti."
        },
    )