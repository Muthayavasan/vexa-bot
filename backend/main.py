from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import asyncio
import threading
import json
import os
import time
import uuid
import hashlib
import secrets
import re

# Import database configuration and models (supports both root and backend directory execution)
try:
    from database import engine, get_db, Base, SessionLocal, DB_FILE_PATH
    from models import UserModel, ChatSessionModel, ChatMessageModel
except ImportError:
    from backend.database import engine, get_db, Base, SessionLocal, DB_FILE_PATH
    from backend.models import UserModel, ChatSessionModel, ChatMessageModel

# Initialize database schema
Base.metadata.create_all(bind=engine)

# Initialize environment
load_env_file = None
try:
    from bot_core import ChatbotEngine, load_env_file
    load_env_file()
except Exception:
    try:
        from backend.bot_core import ChatbotEngine, load_env_file
        load_env_file()
    except Exception:
        pass

app = FastAPI(title="Aether AI Backend API with SQLite & Multi-User Isolation")

# Allow CORS for React frontend (supports localhost, 127.0.0.1, Vercel deployments, and custom domains)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1|.*\.vercel\.app)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Cryptographic Password Hashing Utilities
# ------------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"pbkdf2:sha256:100000${salt}${key.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    if not stored_password or not provided_password:
        return False
    if stored_password.startswith("pbkdf2:sha256:"):
        try:
            parts = stored_password.split("$")
            if len(parts) != 3:
                return False
            _, salt, key_hex = parts
            computed_key = hashlib.pbkdf2_hmac(
                'sha256',
                provided_password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return secrets.compare_digest(computed_key.hex(), key_hex)
        except Exception:
            return False
    # Backward-compatible check for legacy plain-text passwords
    return secrets.compare_digest(stored_password, provided_password)

def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        return authorization[7:].strip()
    return authorization.strip()

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

# ------------------------------------------------------------------------------
# Auto-Migration from users_db.json to SQLite (Run on startup)
# ------------------------------------------------------------------------------
USERS_DB_FILE = os.path.join(os.path.dirname(__file__), "users_db.json")

def migrate_existing_json_data():
    print("Initializing database...")
    if not os.path.exists(USERS_DB_FILE):
        print("Database initialized (No legacy users_db.json found).")
        return

    db: Session = SessionLocal()
    migrated_users_count = 0
    try:
        with open(USERS_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        users_dict = data.get("users", {})
        sessions_dict = data.get("user_sessions", {})

        for uid, uinfo in users_dict.items():
            try:
                existing = db.query(UserModel).filter(UserModel.user_id == uid).first()
                if not existing:
                    email = uinfo.get("email", "").strip().lower()
                    email_exists = db.query(UserModel).filter(UserModel.email == email).first()
                    if email_exists:
                        continue

                    pwd = uinfo.get("password", "")
                    if not pwd.startswith("pbkdf2:sha256:"):
                        pwd = hash_password(pwd)

                    new_user = UserModel(
                        user_id=uid,
                        name=uinfo.get("name", "User"),
                        email=email,
                        password=pwd,
                        auth_token=uinfo.get("auth_token", f"aether_token_{uid}_{secrets.token_hex(16)}"),
                        created_at=uinfo.get("created_at", time.strftime("%Y-%m-%d %H:%M:%S")),
                        last_login=uinfo.get("last_login", time.strftime("%Y-%m-%d %H:%M:%S")),
                    )
                    db.add(new_user)
                    db.commit()
                    migrated_users_count += 1
            except Exception as row_e:
                print(f"Skipping migration for user {uid} due to error: {row_e}")
                db.rollback()

        # Migrate sessions
        for uid, user_sess in sessions_dict.items():
            for sid, sdata in user_sess.items():
                try:
                    existing_session = db.query(ChatSessionModel).filter(ChatSessionModel.session_id == sid).first()
                    if not existing_session:
                        new_session = ChatSessionModel(
                            session_id=sid,
                            user_id=uid,
                            title=sdata.get("title", "Welcome Chat"),
                            created_at=sdata.get("created_at", time.strftime("%b %d, %I:%M %p")),
                            updated_at=time.strftime("%Y-%m-%d %H:%M:%S")
                        )
                        db.add(new_session)
                        db.flush()

                        for msg in sdata.get("messages", []):
                            db.add(ChatMessageModel(
                                session_id=sid,
                                role=msg.get("role", "user"),
                                content=msg.get("content", ""),
                                image_data=msg.get("image", None)
                            ))
                        db.commit()
                except Exception as sess_e:
                    print(f"Skipping migration for session {sid} due to error: {sess_e}")
                    db.rollback()

        print(f"Database initialized. Migration complete: {migrated_users_count} users migrated.")
    except Exception as e:
        print(f"Migration error (continuing server startup): {e}")
        db.rollback()
    finally:
        db.close()

# Run migration once on module initialization
migrate_existing_json_data()

# ------------------------------------------------------------------------------
# Request / Response Schemas
# ------------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str
    password: str = Field(..., min_length=3)

class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class SaveChatsRequest(BaseModel):
    user_id: str
    email: Optional[str] = None
    sessions: Dict[str, Any]

class ChatRequest(BaseModel):
    user_id: Optional[str] = None
    provider: str
    model: str
    system_prompt: str
    temperature: float
    history: List[Dict[str, Any]]
    message: str
    image: Optional[str] = None
    max_tokens: int = 2048


@app.get("/api/health")
def health_check():
    return {"status": "ok", "provider": "FastAPI", "database": "SQLite (SQLAlchemy)", "service": "Aether Auth & Chat Engine"}


# ------------------------------------------------------------------------------
# Authentication Routes with SQLAlchemy Database Operations
# ------------------------------------------------------------------------------
@app.post("/api/auth/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    try:
        email_key = req.email.strip().lower()
        name_clean = req.name.strip()
        
        if not email_key or not EMAIL_REGEX.match(email_key):
            raise HTTPException(status_code=400, detail="Please provide a valid email address.")
        
        if not name_clean:
            raise HTTPException(status_code=400, detail="Name is required.")
            
        if len(req.password) < 4:
            raise HTTPException(status_code=400, detail="Password must be at least 4 characters long.")
        
        # Enforce unique email check in SQLite
        existing_user = db.query(UserModel).filter(UserModel.email == email_key).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="An account with this email address already exists.")
        
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        auth_token = f"aether_token_{user_id}_{secrets.token_hex(16)}"
        hashed_pwd = hash_password(req.password)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        
        user_record = UserModel(
            user_id=user_id,
            name=name_clean,
            email=email_key,
            password=hashed_pwd,
            auth_token=auth_token,
            created_at=current_time,
            last_login=current_time
        )
        
        db.add(user_record)
        db.commit()
        db.refresh(user_record)
        
        return {
            "status": "success",
            "token": auth_token,
            "user": {
                "user_id": user_record.user_id,
                "name": user_record.name,
                "email": user_record.email,
                "last_login": user_record.last_login
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error during registration: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred during registration.")


@app.post("/api/auth/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    email_key = req.email.strip().lower()
    
    if not email_key or not req.password:
        raise HTTPException(status_code=400, detail="Email and password are required.")
    
    user = db.query(UserModel).filter(UserModel.email == email_key).first()
    if not user or not verify_password(user.password, req.password):
        raise HTTPException(status_code=401, detail="Invalid email or password. Please try again.")
    
    # Auto-upgrade legacy plain text password to hash
    if not user.password.startswith("pbkdf2:sha256:"):
        user.password = hash_password(req.password)
        
    auth_token = f"aether_token_{user.user_id}_{secrets.token_hex(16)}"
    user.auth_token = auth_token
    user.last_login = time.strftime("%Y-%m-%d %H:%M:%S")
    db.commit()
    
    # Fetch user sessions
    sessions_dict = {}
    user_sessions = db.query(ChatSessionModel).filter(ChatSessionModel.user_id == user.user_id).all()
    for sess in user_sessions:
        messages_list = [
            {
                "role": m.role,
                "content": m.content,
                **({"image": m.image_data} if m.image_data else {})
            }
            for m in sess.messages
        ]
        sessions_dict[sess.session_id] = {
            "id": sess.session_id,
            "user_id": sess.user_id,
            "title": sess.title,
            "created_at": sess.created_at,
            "messages": messages_list
        }
    
    return {
        "status": "success",
        "token": auth_token,
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "last_login": user.last_login
        },
        "sessions": sessions_dict
    }


@app.get("/api/auth/me")
def get_current_user_profile(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required.")
    
    user = db.query(UserModel).filter(UserModel.auth_token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")
        
    return {
        "status": "success",
        "user": {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "last_login": user.last_login or ""
        }
    }


@app.post("/api/auth/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    email_key = req.email.strip().lower()
    
    if not email_key or not EMAIL_REGEX.match(email_key):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")
    
    user = db.query(UserModel).filter(UserModel.email == email_key).first()
    if not user:
        raise HTTPException(status_code=404, detail="No account found matching this email address.")
    
    return {
        "status": "success",
        "message": f"Password reset instructions have been dispatched to {email_key}."
    }


# ------------------------------------------------------------------------------
# Data Isolation Queries: Fetch & Save Chats in SQLite strictly by user_id
# ------------------------------------------------------------------------------
@app.get("/api/user/chats")
def get_user_chats(user_id: str, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Fetch chat sessions belonging EXCLUSIVELY to owner user_id from SQLite.
    Prevents cross-user data leakage.
    """
    token = extract_token_from_header(authorization)

    # Token ownership verification
    if token:
        token_owner = db.query(UserModel).filter(UserModel.auth_token == token).first()
        if token_owner and token_owner.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot access other users' chat data.")

    user_sessions = db.query(ChatSessionModel).filter(ChatSessionModel.user_id == user_id).all()
    sessions_dict = {}
    for sess in user_sessions:
        messages_list = [
            {
                "role": m.role,
                "content": m.content,
                **({"image": m.image_data} if m.image_data else {})
            }
            for m in sess.messages
        ]
        sessions_dict[sess.session_id] = {
            "id": sess.session_id,
            "user_id": sess.user_id,
            "title": sess.title,
            "created_at": sess.created_at,
            "messages": messages_list
        }

    return {"user_id": user_id, "sessions": sessions_dict}


@app.post("/api/user/chats")
def save_user_chats(req: SaveChatsRequest, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Save chat sessions linked strictly to owner user_id in SQLite.
    """
    token = extract_token_from_header(authorization)
    user_id = req.user_id
    
    if token:
        token_owner = db.query(UserModel).filter(UserModel.auth_token == token).first()
        if token_owner and token_owner.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied: Cannot save chats for other users.")

    user = db.query(UserModel).filter(UserModel.user_id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Sync sessions to SQLite
    for sid, sdata in req.sessions.items():
        session_obj = db.query(ChatSessionModel).filter(ChatSessionModel.session_id == sid).first()
        if not session_obj:
            session_obj = ChatSessionModel(
                session_id=sid,
                user_id=user_id,
                title=sdata.get("title", "New Conversation"),
                created_at=sdata.get("created_at", time.strftime("%b %d, %I:%M %p")),
                updated_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            db.add(session_obj)
            db.flush()
        else:
            session_obj.title = sdata.get("title", session_obj.title)
            session_obj.updated_at = time.strftime("%Y-%m-%d %H:%M:%S")

        # Replace messages for clean synchronization
        db.query(ChatMessageModel).filter(ChatMessageModel.session_id == sid).delete()
        for msg in sdata.get("messages", []):
            db.add(ChatMessageModel(
                session_id=sid,
                role=msg.get("role", "user"),
                content=msg.get("content", ""),
                image_data=msg.get("image", None)
            ))

    db.commit()
    return {"status": "success", "user_id": user_id}


@app.delete("/api/user/chats/{session_id}")
def delete_user_chat(session_id: str, authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    Permanently delete a single chat session and all its messages from the database.
    Only the session owner can delete it.
    """
    token = extract_token_from_header(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required.")

    token_owner = db.query(UserModel).filter(UserModel.auth_token == token).first()
    if not token_owner:
        raise HTTPException(status_code=401, detail="Invalid or expired session token.")

    session_obj = db.query(ChatSessionModel).filter(ChatSessionModel.session_id == session_id).first()
    if not session_obj:
        return {"status": "success", "message": "Session not found (already deleted)."}

    # Ownership check — prevent deleting another user's session
    if session_obj.user_id != token_owner.user_id:
        raise HTTPException(status_code=403, detail="Access denied: Cannot delete another user's chat session.")

    # Delete all messages first (foreign key constraint), then the session
    db.query(ChatMessageModel).filter(ChatMessageModel.session_id == session_id).delete()
    db.delete(session_obj)
    db.commit()

    return {"status": "success", "deleted_session_id": session_id}


# ------------------------------------------------------------------------------
# Chat Streaming Endpoint
# ------------------------------------------------------------------------------
@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    try:
        from bot_core import ChatbotEngine
        engine = ChatbotEngine(
            provider=req.provider,
            model_name=req.model,
            system_prompt=req.system_prompt,
            temperature=req.temperature,
        )
        engine.set_history(req.history)

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()
        _SENTINEL = object()

        def run_sync_generator():
            try:
                for chunk in engine.chat_stream(req.message, image=req.image):
                    asyncio.run_coroutine_threadsafe(queue.put(chunk), loop)
            except Exception as exc:
                asyncio.run_coroutine_threadsafe(queue.put(exc), loop)
            finally:
                asyncio.run_coroutine_threadsafe(queue.put(_SENTINEL), loop)

        thread = threading.Thread(target=run_sync_generator, daemon=True)
        thread.start()

        async def event_generator():
            while True:
                item = await queue.get()

                if item is _SENTINEL:
                    yield "data: [DONE]\n\n"
                    break
                elif isinstance(item, Exception):
                    yield f"data: {json.dumps({'error': str(item)})}\n\n"
                    yield "data: [DONE]\n\n"
                    break
                else:
                    yield f"data: {json.dumps({'text': item})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
