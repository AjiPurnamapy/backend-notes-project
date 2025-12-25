from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

# mengambil 'bagian' dari file yang ingin
from backend.routers import notes, auth
from backend.database import engine
from backend.models import User, Note

# Lifespan: jalan otomatis saat server nyala
@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_db_table()      # perintah: "buat semua tabel yg di-import"
    yield

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        # validasi manual
        if username == "admin" and password == "admin123":
            # simpan tiker di session
            request.session.update({"token": "admin_token_valid"})
            return True
        return False
    
    async def logout(self, request: Request) -> bool:
        # hapus tiket dari session
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False
        return True
    
# inisialisasi keamanan (kunci untuk session browser)
authentication_backend = AdminAuth(secret_key="KUNCI_RAHASIA_AKSES_ADMIN_SESSION")


class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.name, User.age]  # field (kolom) yang ingin di tampilkan
    can_create = True
    can_delete = True
    can_edit = True
    icon = "fa-solid fa-user"  # untuk ikon

class NotesAdmin(ModelView, model=Note):
    column_list = [Note.id, Note.title, Note.content, Note.owner_id]
    can_create = True
    can_edit = True
    can_delete = True
    icon = "fa-solid fa-book"

app = FastAPI(
    title="Notes API Service",
    description="API sederhana untuk menyimpan catatan pribadi dengan fitur login & register",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(auth.router)
app.include_router(notes.router)

admin = Admin(app, engine, authentication_backend=authentication_backend)
admin.add_view(UserAdmin)
admin.add_view(NotesAdmin)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # log error nya hanya bisa dilihat programer
    print(f"FATAL ERROR TERJADI: {exc}")

    # response ke user
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "fail",
            "message": "terjadi kesalahan internal pada server. silahkan coba lagi nanti."
        },
    )