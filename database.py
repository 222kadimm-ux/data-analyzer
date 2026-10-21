import psycopg2
import streamlit as st
import pandas as pd
import json
from tenacity import retry, stop_after_attempt, wait_fixed

# جلب الرابط من الملف السري بأمان
DB_URL = st.secrets["DATABASE_URL"]

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_db_connection():
    """دالة اتصال آمنة مع إعادة المحاولة عند الفشل"""
    return psycopg2.connect(DB_URL)

def init_db():
    """إنشاء الجداول إذا لم تكن موجودة (يُشغل مرة واحدة)"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # جدول المستخدمين مع دور (Role)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # جدول الملفات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_files (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) REFERENCES users(email),
                file_name VARCHAR(255),
                file_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    except Exception as e:
        st.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
    finally:
        cur.close()
        conn.close()

def get_user_role(email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT role FROM users WHERE email = %s", (email,))
        res = cur.fetchone()
        return res[0] if res else "user"
    except:
        return "user"
    finally:
        cur.close()
        conn.close()

def save_file(email, filename, df):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        json_data = df.to_json(orient='records')
        cur.execute("INSERT INTO user_files (user_email, file_name, file_data) VALUES (%s, %s, %s)", 
                    (email, filename, json_data))
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        cur.close()
        conn.close()

def get_files(email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, file_name, file_data, created_at FROM user_files WHERE user_email = %s ORDER BY created_at DESC", (email,))
        return cur.fetchall()
    except Exception:
        return []
    finally:
        cur.close()
        conn.close()

def delete_file(file_id, email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user_files WHERE id = %s AND user_email = %s", (file_id, email))
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()
