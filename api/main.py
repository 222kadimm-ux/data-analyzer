from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import bcrypt
import os
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI()

# إعداد CORS للسماح لـ React (Netlify) بالاتصال
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # في الإنتاج، ضع رابط Netlify هنا
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.getenv("DATABASE_URL")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def get_db():
    return psycopg2.connect(DB_URL)

# نماذج البيانات (Pydantic)
class UserAuth(BaseModel):
    email: str
    password: str

class AIRequest(BaseModel):
    question: str
    data_summary: str

# ================= نقاط النهاية (Endpoints) =================

@app.get("/")
def read_root():
    return {"status": "API is running"}

@app.post("/api/auth/register")
def register(user: UserAuth):
    conn = get_db()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cur.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'user')", (user.email, hashed))
        conn.commit()
        return {"message": "User created successfully"}
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Email already exists")
    finally:
        cur.close()
        conn.close()

@app.post("/api/auth/login")
def login(user: UserAuth):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE email = %s", (user.email,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result and bcrypt.checkpw(user.password.encode('utf-8'), result[0].encode('utf-8')):
        return {"message": "Login successful", "email": user.email}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/analyze")
def analyze(req: AIRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=500, detail="API Key missing")
        
    prompt = f"""
    أنت محلل بيانات خبير. لديك بيانات بهذا الملخص:
    {req.data_summary}
    
    المستخدم يسأل: "{req.question}"
    أجب باللغة العربية.
    """
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        answer = response.json()['choices'][0]['message']['content']
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
