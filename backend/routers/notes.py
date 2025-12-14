from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Notes, User
from dependencies import get_current_user

router = APIRouter(
    prefix="/notes",    # semua URl diisi otomatis depannya/catatan
    tags=["Notes"]      # biar rapi
)

@router.post("/", response_model=Notes)
def create_notes(
    note: Notes,
    session: Session = Depends(get_session),
    current_user : User = Depends(get_current_user),
):
    note.owner_id = current_user.id  # membuat paksa owner_id disamakan dengan user_id saat ini
    
    session.add(note)
    session.commit()
    session.refresh(note)
    return note

@router.get("/", response_model=List[Notes])
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

@router.put("/{notes_id}", response_model=Notes)
def update_notes(notes_id:int, new_notes:Notes,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes_db = session.get(Notes, notes_id)

    if not notes_db:
        raise HTTPException(status_code=404, detail="notes not found")
    
    if notes_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="youre not allowed")
    
@router.delete("/{notes_id}")
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
