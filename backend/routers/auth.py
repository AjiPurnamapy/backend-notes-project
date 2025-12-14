from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from database import get_session
from models import User
from dependencies import get_password_hash, verify_password, create_acces_token, get_current_user

router = APIRouter(tags=["Authentication"])

@router.post("/user", response_model=User)
def create_user(user: User, session: Session = Depends(get_session)):
    # hash password dan timpa password asli dengan yang sudah diacak
    user.password = get_password_hash(user.password)

    session.add(user)        # menyimpan data ke memori python
    session.commit()         # mengirim datanya ke database
    session.refresh(user)    # mengambil data yang tadi dari database
    return user              # menampilkan data ke user


@router.post("/token")
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

# endpoint khusus data pribadi user
@router.get("/myprofile", response_model=User)
def check_my_profile(current_user : User = Depends(get_current_user)):
    return current_user