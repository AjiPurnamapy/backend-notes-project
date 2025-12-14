from datetime import datetime, timedelta, timezone # untuk menambahkan waktu dan batas waktu
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer  # Untuk form login
from sqlmodel import Session, select
from passlib.context import CryptContext    # untuk mengubah password
from jose import JWTError, jwt 
from database import get_session
from models import User

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