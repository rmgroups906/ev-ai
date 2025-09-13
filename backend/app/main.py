import os
from fastapi import (
    FastAPI, Depends, HTTPException, WebSocket, 
    WebSocketDisconnect, status, Request
)
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse 
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
from . import security, crud, models, schemas, services, ml
from .config import settings
from .db import init_db, SessionLocal
from .logging_config import logger
from .model import AnomalyModel
from .error_handlers import (
    custom_http_exception_handler,
    validation_exception_handler,
    global_exception_handler,
)
app = FastAPI(title=settings.APP_NAME)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handles responses for requests that exceed the defined rate limit."""
    logger.warning(f"Rate limit exceeded for {request.client.host}", extra={"url": str(request.url)})
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded. Try again in {exc.detail}."},
    )

app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
anomaly_model = AnomalyModel()

@app.on_event('startup')
async def startup():
    """Initializes the database and loads the ML model on startup."""
    logger.info("Application starting up...")
    init_db()
    
    model_path = os.path.join(settings.MODELS_DIR, 'model_iforest.joblib')
    if os.path.exists(model_path):
        if anomaly_model.load(model_path):
            logger.info(f"Anomaly detection model loaded successfully from {model_path}")
        else:
            logger.warning(f"Could not load anomaly detection model from {model_path}")
    else:
        logger.warning("No anomaly detection model found. Telemetry endpoint will not perform predictions.")
    logger.info("Startup complete.")

def get_db():
    """FastAPI dependency that provides and properly closes a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health", tags=["General"])
def health_check():
    """A simple endpoint to confirm the API is running."""
    return {"status": "ok"}

@app.post('/auth/register', response_model=dict, status_code=status.HTTP_201_CREATED, tags=["Auth"])
@limiter.limit("5/minute")
async def register(request: Request, u: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user."""
    logger.info(f"Registration attempt for username: {u.username}")
    existing = crud.get_user_by_username(db, u.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Username already exists')
    
    user = crud.create_user(db, u)
    logger.info(f"User '{user.username}' created successfully.")
    return {'username': user.username, 'role': user.role}

@app.post('/auth/token', response_model=schemas.TokenWithRefresh, tags=["Auth"])
@limiter.limit("10/minute")
async def login_for_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Provides JWT access and refresh tokens for valid credentials."""
    logger.info(f"Token requested for user: {form_data.username}")
    user = security.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')
    
    token_data = {'sub': user.username, 'role': user.role}
    access_token = security.create_access_token(token_data)
    refresh_token = security.create_refresh_token(token_data)
    
    logger.info(f"Tokens generated for user: {form_data.username}")
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'bearer'
    }


@app.post('/auth/refresh', response_model=schemas.Token, tags=["Auth"])
@limiter.limit("5/minute")
async def refresh_access_token(request: Request, refresh_request: schemas.RefreshToken, db: Session = Depends(get_db)):
    """Refreshes an access token using a valid refresh token."""
    username = security.verify_refresh_token(db, refresh_request.refresh_token)
    user = crud.get_user_by_username(db, username)
    if not user:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    access_token = security.create_access_token({'sub': user.username, 'role': user.role})
    logger.info(f"Access token refreshed for user: {username}")
    return {'access_token': access_token, 'token_type': 'bearer'}

@app.get("/users/me", response_model=schemas.User, tags=["Users"])
def read_users_me(current_user: models.User = Depends(security.get_current_user)):
    """Fetches the profile of the currently authenticated user."""
    return current_user

@app.post('/train/parts', status_code=status.HTTP_202_ACCEPTED, tags=["ML"])
async def train_parts(user: models.User = Depends(security.get_current_admin_user)):
    """Triggers the training process for the parts anomaly model."""
    csv_path = 'app/data/parts_labeled.csv'
    logger.info(f"Parts training process triggered by user '{user.username}'. Using data from '{csv_path}'")
    
    p = ml.trainer.train_parts(csv_path)
    logger.info(f"Training successful. Model saved to: {p}")
    return {'status': 'training_completed', 'path': p}


@app.post('/telemetry', tags=["ML"])
async def telemetry(t: schemas.Telemetry, user: models.User = Depends(security.get_current_user)):
    """Receives telemetry data and performs anomaly detection if a model is loaded."""
    score, label = None, None
    
    if anomaly_model.is_loaded():
        feat = anomaly_model.prepare_features_single(t.dict())
        score = anomaly_model.score(feat.reshape(1, -1))[0]
        label = anomaly_model.predict(feat.reshape(1, -1))[0]
        logger.info(f"Telemetry from vehicle {t.vehicle_id} processed.", extra={"score": score, "label": label})
    else:
        logger.info(f"Received telemetry from vehicle {t.vehicle_id}, but no model is loaded for analysis.")
    
    return {'telemetry': t.dict(), 'score': score, 'label': label}


@app.post('/tickets', response_model=schemas.Ticket, status_code=status.HTTP_201_CREATED, tags=["Tickets"])
async def create_ticket(req: schemas.TicketCreate, user: models.User = Depends(security.get_current_user), db: Session = Depends(get_db)):
    """Creates a new ticket and assigns it to the technician with the fewest open tickets."""
    logger.info(f"Ticket creation request received for vehicle_id: {req.vehicle_id}")
    ticket = await services.ticket_service.create_and_assign_ticket(db, req)
    logger.info(f"Ticket {ticket.id} created and assigned to user_id: {ticket.assigned_to}")
    return ticket

@app.websocket('/ws/stream')
async def ws_stream(websocket: WebSocket):
    """Handles WebSocket connections for real-time data streaming."""
    token = websocket.query_params.get('token')
    username = "unknown" 
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        payload = security.decode_token(token)
        username = payload.get("sub", "unknown") 
        logger.info(f"WebSocket connection accepted for user: {username}")
        await websocket.accept()
        while True:
            await websocket.receive_text()
            await websocket.send_text('ack')
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for user: {username}")
    except Exception:
        logger.warning(f"WebSocket connection for user {username} closed due to an error.", exc_info=True)
        if not websocket.client_state == 'DISCONNECTED':
             await websocket.close(code=status.WS_1008_POLICY_VIOLATION)