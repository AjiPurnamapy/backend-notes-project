from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from database import get_session
from schemas.user import UserCreate, UserRead
from models import User
from dependencies import get_password_hash, verify_password, create_acces_token, get_current_user

router = APIRouter(tags=["Authentication"])

@router.post("/register", response_model=UserRead)
def create_user(user_input: UserCreate, session: Session = Depends(get_session)):
    # validasi username
    existing_user = session.exec(select(User).where(User.name ==user_input.name)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="username sudah dipakai")
    
    # konversi dari UserCreate (schema) ke User (model database)
    user_db = User.model_validate(user_input)
    # hash password dan timpa password asli dengan yang sudah diacak
    user_db.password = get_password_hash(user_input.password)

    session.add(user_db)        # menyimpan data ke memori python
    session.commit()            # mengirim datanya ke database
    session.refresh(user_db)    # mengambil data yang tadi dari database
    return user_db              # menampilkan data ke user


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
@router.get("/myprofile", response_model=UserRead)
def check_my_profile(current_user : User = Depends(get_current_user)):
    return current_user