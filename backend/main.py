from datetime import datetime, timedelta, timezone # untuk menambahkan waktu dan batas waktu
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm  # Untuk form login
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from passlib.context import CryptContext    # untuk mengubah password
from jose import JWTError, jwt  # untuk buat token 

# mengambil 'bagian' dari file yang ingin
from database import create_db_table, get_session
from models import User, Notes

# konfigurasi keamanan dan kunci rahasia
SECRET_KEY = "developer_ganteng_suaminya_waguri"
ALGORITHM = "HS256"
ACCES_TOKEN_EXPIRE_MINUTES = 30  # batas waktu penggunaan token (menit)

# konfigurasi dan seting agar menggunakan algoritma bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str : # ' -> ' keluaran berupa string
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_acces_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCES_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# dependency pengecekan token
def get_current_user(token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
):
    # baca tokennya (decode)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kadaluarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")  # mengambil nama user dari dalam token 
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    # untuk memastikan data user masih ada, tidak dihapus (admin)
    statement = select(User).where(User.name == username)
    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user

# Lifespan: jalan otomatis saat server nyala
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_table() # perintah: "buat semua tabel yg di-import"
    yield

app = FastAPI(lifespan=lifespan)

# endpoint khusus data pribadi user
@app.get("/my_profile", response_model=User)
def check_my_profile(current_user : User = Depends(get_current_user)):
    return current_user

@app.post("/my_notes", response_model=Notes)
def check_my_notes(
    note: Notes,
    session: Session = Depends(get_session),
    current_user : User = Depends(get_current_user),
):
    note.owner_id = current_user.id
    
    session.add(note)
    session.commit()
    session.refresh(note)
    return note

@app.get("/my_notes", response_model=list[Notes])
def read_my_notes(
    q: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user : User = Depends(get_current_user),
):
    # set untuk menampilkan yg hanya milik user
    statement = select(Notes).where(Notes.owner_id == current_user.id)

    # cari berdasarkan judul atau isi
    if q:
        statement = statement.where(
            (Notes.title.contains(q)) | (Notes.content.contains(q))
        )

    result = session.exec(statement).all()
    return result

@app.post("/token")
def login_for_acces_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
    ):
    # cari user di database berdasarkan username 
    statement = select(User).where(User.name == form_data.username)
    user = session.exec(statement).first()
    
    # cek user ada atau tidak, cek password cocok atau tidak
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # jika lolos, buatkan token
    access_token = create_acces_token(data={"sub": user.name})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/user", response_model=User)
def create_user(user: User, session: Session = Depends(get_session)):
    # hash password dan timpa password asli dengan yang sudah diacak
    user.password = get_password_hash(user.password)

    session.add(user)        # menyimpan data ke memori python
    session.commit()         # mengirim datanya ke database
    session.refresh(user)    # mengambil data yang tadi dari database
    return user              # menampilkan data ke user

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

@app.put("/notes/{notes_id}", response_model=Notes)
def update_notes(notes_id:int, new_notes:Notes,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes_db = session.get(Notes, notes_id)

    if not notes_db:
        raise HTTPException(status_code=404, detail="notes not found")
    
    if notes_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="youre not allowed")


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

@app.delete("/notes/{notes_id}")
def delete_notes(
    notes_id :int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # mencari catatan di database
    notes_db = session.get(Notes, notes_id)

    # catatan ada/tidak?
    if not notes_db:
        raise HTTPException(status_code=403, detail="notes not found")
    
    # cek apakah pemilik catatan (id), sama dengan (id) user yg saat ini login?
    if notes_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your own notes")


    session.delete(notes_db)
    session.commit()
    return{"messege": "notes deleted"}