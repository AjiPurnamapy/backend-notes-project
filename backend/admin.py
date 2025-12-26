import os
import time
from dotenv import load_dotenv
from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse
from backend.models import User, Note

load_dotenv()
USERNAME_ADMIN = os.getenv("USERNAME_ADMIN")
PASSWORD_ADMIN = os.getenv("PASSWORD_ADMIN")
TOKEN_ADMIN = os.getenv("TOKEN_ADMIN")
SECRET_KEY_ADMIN = os.getenv("SECRET_KEY_ADMIN_SESSION")
MAX_SESSION_TIME = 3600 
# cek kelengkapan konfigurasi
if not all([USERNAME_ADMIN, PASSWORD_ADMIN, TOKEN_ADMIN, SECRET_KEY_ADMIN]):
    raise ValueError ("Fatal Error Terjadi, Konfigurasi Di Admin Kurang lengkap ")

class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        # validasi manual hardcode (bisa di ganti .env)
        if username == USERNAME_ADMIN and password == PASSWORD_ADMIN:
            # simpan tiket di session
            request.session.update({
                "token": TOKEN_ADMIN,
                "login_time": time.time()
                })
            return True
        return False
    
    async def logout(self, request: Request) -> bool:
        # hapus tiket dari session
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        login_time = request.session.get("login_time") 
    
        if not token or token != TOKEN_ADMIN:
            return False
        
        if not login_time:
            return False
        
        if time.time() - login_time > MAX_SESSION_TIME:
            request.session.clear()
            return False
        
        return True
    

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

def setup_admin(app, engine):
    # inisialisasi keamanan (kunci untuk session browser)
    authentication_backend = AdminAuth(secret_key=SECRET_KEY_ADMIN)

    admin = Admin(app, engine, authentication_backend=authentication_backend)
    admin.add_view(UserAdmin)
    admin.add_view(NotesAdmin)