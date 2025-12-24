from typing import List
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from contextlib import asynccontextmanager

# mengambil 'bagian' dari file yang ingin
from backend.routers import notes, auth
from backend.database import get_session
from backend.models import User
from backend.schemas.user import BaseUser
from backend.dependencies import (
    get_current_user,
    get_password_hash,
)

# Lifespan: jalan otomatis saat server nyala
@asynccontextmanager
async def lifespan(app: FastAPI):
    # create_db_table()      # perintah: "buat semua tabel yg di-import"
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(notes.router)

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

@app.get("/user", response_model=List[User])
def read_all_user(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    print (f"yang sedang akses adalah: {current_user.name}")   # debugging di terminal
    statement = select(User)
    result = session.exec(statement).all()
    return result


@app.put("/user{user_id}", response_model= BaseUser)
def update_user(user_id: int, new_data: User,
    session: Session = Depends(get_session),
):
    # cari data lama di database dan buat variabel
    user_db = session.get(User, user_id)         # 'user_db' sebagai perwakilan (copy-an) dari data asli (database)
    
    # validasi ada atau tidak, "no? = error 404"
    if not user_db:
        raise HTTPException(status_code=404, detail="user not found")
    
    # update data (mengganti data lama (copy-an) dengan data baru)
    if new_data.password:
        new_hashed_password = get_password_hash(new_data.password)   # untuk meng-hash password baru yg di inputkan user
    
    user_db.id = new_data.id
    user_db.name = new_data.name
    user_db.age = new_data.age
    user_db.password = new_hashed_password

    #simpan perubahan
    session.add(user_db)        # menyimpan data ke memori python
    session.commit()            # mengirim datanya ke database (menimpa data asli yang ada di database)
    session.refresh(user_db)    # mengambil data yang baru di ubah dari database
    return user_db             # menampilkan data yg baru saja di ubah ke user


@app.delete("/user{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    # masih sama, cari datanya
    user_db = session.get(User, user_id)
    #validasi lagi
    if not user_db:
        raise HTTPException(status_code=404, detail="user not found")
    
    #hapus datanya
    session.delete(user_db) # menghapus data sesuai request (user) di database
    session.commit() # menyimpan perubahan
    return {"message": "data has deleted succsesfully "}
