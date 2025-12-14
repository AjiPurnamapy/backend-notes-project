from typing import List
from fastapi import FastAPI, HTTPException, Depends
from sqlmodel import Session, select
from contextlib import asynccontextmanager

# mengambil 'bagian' dari file yang ingin
from routers import notes, auth
from database import create_db_table, get_session
from models import User
from dependencies import (
    get_current_user,
    get_password_hash,
)

# Lifespan: jalan otomatis saat server nyala
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_table() # perintah: "buat semua tabel yg di-import"
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(notes.router)

@app.get("/user", response_model=List[User])
def read_user(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    print (f"yang sedang akses adalah: {current_user.name}")   # debugging di terminal
    statement = select(User)
    result = session.exec(statement).all()
    return result


@app.put("/user/{user_id}", response_model= User)
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
    return user_db              # menampilkan data yg baru saja di ubah ke user


@app.delete("/user/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    # masih sama, cari datanya
    user_db = session.get(User, user_id)
    #validasi lagi
    if not user_db:
        raise HTTPException(status_code=404, detail="user not found")
    
    #hapus datanya
    session.delete(user_db) # menghapus data sesuai request (user) di database
    session.commit() # menyimpan perubahan
    return {"messege": "data has deleted succsesfully "}

print("-daftaru route")
for route in app.routes:
    print(route.path)
print("___________")