from sqlalchemy.orm import Session
from . import models, security
from .schemas import UserCreate

def create_user(db: Session, user: dict):
    hashed = security.get_password_hash(user['password'])
    u = models.User(username=user['username'], hashed_password=hashed, role=user.get('role','driver'), email=user.get('email'), phone=user.get('phone'))
    db.add(u); db.commit(); db.refresh(u); return u

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username==username).first()

def list_technicians(db: Session):
    return db.query(models.User).filter(models.User.role=='technician').all()