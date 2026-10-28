import psycopg2
import streamlit as st
import pandas as pd
import json
from settings import DATABASE_URL
from tenacity import retry, stop_after_attempt, wait_fixed

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_db_connection():
    if not DATABASE_URL:
        st.error("⚠️ DATABASE_URL غير موجود في الإعدادات.")
        st.stop()
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_files (
                id SERIAL PRIMARY KEY,
                user_email VARCHAR(255) NOT NULL,
                file_name VARCHAR(255),
                file_data JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cur.execute("ALTER TABLE user_files DROP CONSTRAINT IF EXISTS user_files_user_email_fkey;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_files_email ON user_files(user_email);")
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
    except Exception:
        return "user"
    finally:
        cur.close()
        conn.close()

def save_file(email, filename, df):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        json_data = df.to_json(orient='records', date_format='iso')
        cur.execute("INSERT INTO user_files (user_email, file_name, file_data) VALUES (%s, %s, %s)", 
                    (email, filename, json_data))
        conn.commit()
        return True
    except Exception as e:
        st.warning(f"⚠️ تعذر حفظ الملف: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_files(email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # العزل: جلب ملفات هذا المستخدم فقط
        cur.execute("SELECT id, file_name, file_data, created_at FROM user_files WHERE user_email = %s ORDER BY created_at DESC", (email,))
        return cur.fetchall()
    except:
        return []
    finally:
        cur.close()
        conn.close()

def get_file_by_id(file_id, email):
    # العزل: جلب ملف محدد مع التحقق من أنه يخص المستخدم
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, file_name, file_data FROM user_files WHERE id = %s AND user_email = %s", (file_id, email))
        return cur.fetchone()
    except:
        return None
    finally:
        cur.close()
        conn.close()

def delete_file(file_id, email):
    # العزل: الحذف فقط إذا كان الملف يخص المستخدم
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
