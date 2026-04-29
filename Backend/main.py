"""
Granite Guardian – Predictive Maintenance Advisor API
=====================================================
Main application entry point.
Mounts all route modules and registers middleware.

Run with:  uvicorn main:app --reload
Docs at:   http://localhost:8000/docs  (Swagger UI)
"""
from collections.abc import Iterable
from fastapi.responses import StreamingResponse
from config import GRANITE_MODEL, MODELS_PATH
from datetime import datetime
from typing import Optional
from sqlalchemy import desc
from models.chat import ChatSession, ChatMessage
import os
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
import ollama
from routes import upload_routes, data_routes, diagnostics_routes, alert_routes, granite_routes
from pydantic import BaseModel
from services import user_service
from fastapi import Response, HTTPException
from services.auth_service import verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

from services import auth_service
from middleware.error_handler import register_error_handlers
from middleware.security import SecurityHeadersMiddleware
from middleware.rate_limiter import register_rate_limiter
from middleware.request_logger import RequestLoggerMiddleware
import time

# grab granite model
ollama_running = False

while not ollama_running:
    try:
        ollama.list()
        ollama_running = True
    except:
        print("Ollama not running, trying again in 2 seconds...")
        time.sleep(2)

print(f"Pulling Granite model ({GRANITE_MODEL}), this may take a while...")

try:
    ollama.pull(GRANITE_MODEL)
    print(f"Finished pulling Granite model ({GRANITE_MODEL}).")
except:
    print("Failed to pull Granite model (perhaps model does not exist?).")
    print("AI chatbot features will not work!")

#Logging 
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("granite_guardian")

#App initialisation 
app = FastAPI(
    title="Granite Guardian API",
    description="Predictive Maintenance Advisor – analyse OBD-II vehicle sensor data "
                "and receive natural-language maintenance guidance.",
    version="1.0.0",
)

# Middleware stack:
# CORS
app.add_middleware(
    CORSMiddleware,
    # Use your real frontend URL here
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#Security headers
app.add_middleware(SecurityHeadersMiddleware)
#Request logging
app.add_middleware(RequestLoggerMiddleware)
# 4. Rate limiting
register_rate_limiter(app)

#Error handlers 
register_error_handlers(app)

#Ensure required directories exist on startup
os.makedirs("./uploaded_data", exist_ok=True)
os.makedirs("./logs", exist_ok=True)

#  AUTH ROUTES 
class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str


@app.post("/auth/register", tags=["Authentication"])
async def register(
    req: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new user"""
    return await auth_service.register_user(req.username, req.email, req.password, db)

class UserLoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login", tags=["Authentication"])
async def login(
    req: UserLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    # """Login and get JWT token"""
    # return await auth_service.login_user(req.email, req.password, db)
    #
    # Find user
    user = user_service.get_user_by_email(db, req.email)
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_access_token({"sub": user.username})

    # Set cookie (HTTP-only)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production with HTTPS
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    );

    return {
        "message": "Login successful",
    };

@app.post("/auth/logout", tags=["Authentication"])
async def logout(response: Response):
    """Logout by clearing the auth cookie"""
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Logout successful"}


@app.get("/auth/me", tags=["Authentication"])
async def get_current_user(
    current_user = Depends(auth_service.get_current_user)
):
    """Get current user info"""
    return current_user

class CreateChatSessionRequest(BaseModel):
    # Optional title for a new chat session
    title: Optional[str] = "New Chat"


class ChatRequest(BaseModel):
    # Which saved chat session this message belongs to
    session_id: int

    # New message typed by the user
    message: str


@app.post("/chat/sessions", tags=["AI Chatbot"])
async def create_chat_session(
    payload: CreateChatSessionRequest,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    # Create a new empty chat linked to the current user
    new_session = ChatSession(
        user_id=current_user.id,
        title=(payload.title or "New Chat").strip() or "New Chat",
        created_at=datetime.utcnow()
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return {
        "id": new_session.id,
        "title": new_session.title,
        "created_at": new_session.created_at
    }


@app.get("/chat/sessions", tags=["AI Chatbot"])
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    # Return only chats that belong to the logged-in user
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(desc(ChatSession.created_at))
        .all()
    )

    return [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at
        }
        for session in sessions
    ]


@app.get("/chat/sessions/{session_id}/messages", tags=["AI Chatbot"])
async def get_chat_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    # Make sure the user is only allowed to read their own chat
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "id": msg.id,
            "role": "bot" if msg.role == "assistant" else msg.role,
            "content": msg.content,
            "created_at": msg.created_at
        }
        for msg in messages
    ]

@app.delete("/chat/sessions/{session_id}", tags=["AI Chatbot"])
async def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    """
    Deletes an entire chat session.

    Because ChatSession has cascade="all, delete-orphan",
    deleting the session automatically deletes all messages
    linked to it.
    """

    # First make sure the session exists and belongs to this user
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Delete the chat session
    db.delete(session)
    db.commit()

    return {"message": "Chat deleted successfully"}

@app.post("/chat", tags=["AI Chatbot"], response_class=StreamingResponse, response_model=None)
def chat_with_granite(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
):
    return StreamingResponse(chat_with_granite_impl(payload, db, current_user), media_type="text/plain")

def chat_with_granite_impl(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(auth_service.get_current_user)
) -> Iterable[str]:
    user_message = payload.message.strip()

    # Reject blank messages
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check that the selected session belongs to the current user
    session = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == payload.session_id,
            ChatSession.user_id == current_user.id
        )
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    try:
        # Save the user's message into the database
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=user_message,
            created_at=datetime.utcnow()
        )
        db.add(user_msg)
        db.commit()

        # Load chat history so the model can remember context
        history = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        # Keep the context smaller so the tiny model stays responsive
        recent_history = history[-12:]

        ollama_messages = [
            {
                "role": "system",
                "content": "You are Granite Guardian, a professional automotive expert. Explain OBD-II data simply."
            }
        ]

        for msg in recent_history:
            ollama_messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # send message to ollama
        response = ollama.chat(
            model=GRANITE_MODEL,
            messages=ollama_messages,
            stream=True
        )

        assistant_reply  = ""
        for chunk in response:
            assistant_reply += chunk["message"]["content"]
            print(f"{chunk["message"]["content"]}")
            yield chunk["message"]["content"]

        # Save the assistant reply too
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_reply,
            created_at=datetime.utcnow()
        )
        db.add(assistant_msg)

        # Rename the chat after the first real message
        if session.title == "New Chat":
            words = user_message.split()
            session.title = " ".join(words[:6]) if words else "New Chat"

        db.commit()

        #return {
        #    "reply": assistant_reply,
        #    "session_id": session.id
        #}

    except Exception as e:
        print(f"OLLAMA CRASH REASON: {str(e)}")
        #return {"reply": f"Granite Connection Error: {str(e)}"}


# Mount their routers
app.include_router(upload_routes.router)
app.include_router(data_routes.router)
app.include_router(diagnostics_routes.router)
app.include_router(alert_routes.router)
app.include_router(granite_routes.router)

# Health check 
@app.get("/", tags=["Health"])
async def health_check():
    """API health check endpoint."""
    return {
        "status": "ok",
        "service": "Granite Guardian API",
        "version": "1.0.0",
    }



