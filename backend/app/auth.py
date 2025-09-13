from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from passlib.context import CryptContext
import jwt
import secrets

SECRET_KEY = "your-super-secret-key-loaded-from-env" # e.g., settings.SECRET_KEY
REFRESH_SECRET_KEY = "your-super-secret-refresh-key-loaded-from-env" # e.g., settings.REFRESH_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hashes a plain password."""
    return pwd_context.hash(password)


def create_access_token(data: dict) -> str:
    """Creates a new JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Creates a new JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

def verify_refresh_token(token: str) -> str:
    """
    Verifies a refresh token and returns the user's ID (subject).
    Raises HTTPException if the token is invalid, expired, or malformed.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return user_id
    except jwt.PyJWTError:
        raise credentials_exception


def create_password_reset_token_for_user(db, user) -> str:
    """
    Generates a password reset token, stores its hash in the database,
    and returns the plaintext token.
    """
    plaintext_token = secrets.token_urlsafe(32)
    user.reset_token = get_password_hash(plaintext_token)
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()
    return plaintext_token

def reset_password_with_token(db, token: str, new_password: str) -> bool:
    """
    Finds a user by a valid reset token, updates their password,
    and invalidates the token. Returns True on success.
    """
    active_tokens_users = db.query(User).filter(User.reset_token_expires_at > datetime.now(timezone.utc)).all()
    
    user_to_update = None
    for user in active_tokens_users:
        if verify_password(token, user.reset_token):
            user_to_update = user
            break

    if not user_to_update:
        return False
    user_to_update.hashed_password = get_password_hash(new_password)
    user_to_update.reset_token = None
    user_to_update.reset_token_expires_at = None
    db.commit()
    return True