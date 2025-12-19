from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from schemas.notes import ReadNotes, CreateNotes
from database import get_session
from models import Notes, User
from dependencies import get_current_user

router = APIRouter(
    prefix="/notes",    # semua URl diisi otomatis depannya/catatan
    tags=["Notes"]      # biar rapi
)

@router.post("/", response_model=ReadNotes)
def create_notes(
    notes_input: CreateNotes,
    session: Session = Depends(get_session),
    current_user : User = Depends(get_current_user),
):
    note_dict = notes_input.model_dump()
    note_dict["owner_id"] = current_user.id

    notes_db = Notes.model_validate(note_dict)
    
    session.add(notes_db)
    session.commit()
    session.refresh(notes_db)
    return notes_db

@router.get("/", response_model=List[ReadNotes])
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

@router.put("/{notes_id}", response_model=ReadNotes)
def update_notes(notes_id:int, new_notes:CreateNotes,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    notes_db = session.get(Notes, notes_id)

    if not notes_db:
        raise HTTPException(status_code=404, detail="notes not found")
    
    if notes_db.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="youre not allowed")
    
    notes_db.title = new_notes.title
    notes_db.content = new_notes.content

    session.add(notes_db)
    session.commit()
    session.refresh(notes_db)
    return notes_db


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
