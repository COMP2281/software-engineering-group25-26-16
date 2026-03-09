"""
Granite Guardian – Predictive Maintenance Advisor API
=====================================================
Main application entry point.
Mounts all route modules and registers middleware.

Run with:  uvicorn main:app --reload
Docs at:   http://localhost:8000/docs  (Swagger UI)
"""

import os
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db
import ollama
from fastapi import Body
from routes import upload_routes, data_routes, diagnostics_routes, alert_routes, granite_routes

from services import auth_service
from middleware.error_handler import register_error_handlers
from middleware.security import SecurityHeadersMiddleware
from middleware.rate_limiter import register_rate_limiter
from middleware.request_logger import RequestLoggerMiddleware

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
    allow_origins=["*"],# tighten for production
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
@app.post("/auth/register", tags=["Authentication"])
async def register(
    username: str, 
    email: str, 
    password: str,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    return await auth_service.register_user(username, email, password, db)

@app.post("/auth/login", tags=["Authentication"])
async def login(
    username: str, 
    password: str,
    db: Session = Depends(get_db)
):
    """Login and get JWT token"""
    return await auth_service.login_user(username, password, db)

@app.get("/auth/me", tags=["Authentication"])
async def get_current_user(
    current_user = Depends(auth_service.get_current_user)
):
    """Get current user info"""
    return current_user


@app.post("/chat", tags=["AI Chatbot"])
async def chat_with_granite(payload: dict = Body(...)):
    user_message = payload.get("message")
    
    try:
        response = ollama.chat(model='granite3-dense:8b', messages=[
            {
                'role': 'system',
                'content': 'You are Granite Guardian, a professional automotive expert. Explain OBD-II data simply.'
            },
            {
                'role': 'user',
                'content': user_message
            }
        ])
        return {"reply": response['message']['content']}
        
    except Exception as e:
        return {"reply": "Connection to Granite failed. Make sure the Ollama app is running on your Mac."} 
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

@app.post("/chat", tags=["AI Chatbot"])
async def chat_with_granite(payload: dict = Body(...)):
    user_message = payload.get("message")
    
    try:
        response = ollama.chat(model='granite3-dense:8b', messages=[
            {
                'role': 'system',
                'content': 'You are Granite Guardian, a professional automotive expert. Explain OBD-II data simply.'
            },
            {
                'role': 'user',
                'content': user_message
            }
        ])
        return {"reply": response['message']['content']}
        
    except Exception as e:
        print(f"OLLAMA CRASH REASON: {str(e)}")
        # This will show the exact error in your Chatbot UI
        return {"reply": f"Granite Connection Error: {str(e)}"}

