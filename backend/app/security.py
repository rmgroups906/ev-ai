from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .config import settings
from .db import SessionLocal
from . import models

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({'exp': expire})
    # use primary key to sign
    key = settings.SECRET_KEYS[0]
    encoded = jwt.encode(to_encode, key, algorithm=settings.ALGORITHM)
    return encoded

def decode_token(token: str):
    # try each key for rotation support
    last_exc = None
    for key in settings.SECRET_KEYS:
        try:
            payload = jwt.decode(token, key, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError as e:
            last_exc = e
    raise HTTPException(status_code=401, detail='Could not validate credentials')

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.User).filter(models.User.username==username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_token(token)
    username = payload.get('sub')
    if username is None:
        raise HTTPException(status_code=401, detail='Invalid token payload')
    user = db.query(models.User).filter(models.User.username==username).first()
    if user is None:
        raise HTTPException(status_code=401, detail='User not found')
    return user