from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import psycopg2
import bcrypt
import os
import requests
from datetime import datetime, timedelta
from jose import JWTError, jwt

# --- إعدادات الأمان ---
SECRET_KEY = os.getenv("API_TOKEN_SECRET", "default-secret-key-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480 # 8 ساعات

# --- إعدادات CORS ---
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "https://data-analyzer-vzl8jspasawmzxey7gezcm.streamlit.app").split(",")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (باقي الكود الخاص بك، مثل نماذج Pydantic ونقاط النهاية) ...
