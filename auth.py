import streamlit as st
import bcrypt
from database import get_db_connection, get_user_role

def create_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # التعديل: جميع المستخدمين الجدد "user" فقط
    role = "user"
    
    try:
        cur.execute("INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)", (email, hashed, role))
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

def verify_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
        result = cur.fetchone()
        if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            return True
        return False
    except:
        return False
    finally:
        cur.close()
        conn.close()

def login_user(email):
    st.session_state.logged_in = True
    st.session_state.user_email = email
    st.session_state.user_role = get_user_role(email)

def logout_user():
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_role = None
    st.session_state.df = None
    st.rerun()
