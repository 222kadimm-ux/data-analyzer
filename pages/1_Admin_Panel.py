import streamlit as st
from database import get_db_connection

st.set_page_config(page_title="Admin Panel", page_icon="👑")
st.title("👑 لوحة تحكم المدير")

if not st.session_state.get("logged_in") or st.session_state.get("user_role") != "admin":
    st.error("🚫 غير مصرح لك بالدخول.")
    st.stop()

st.success("مرحباً أيها المدير.")
conn = get_db_connection()
cur = conn.cursor()
try:
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM user_files")
    total_files = cur.fetchone()[0]
    c1, c2 = st.columns(2)
    c1.metric("إجمالي المستخدمين", total_users)
    c2.metric("إجمالي الملفات", total_files)
finally:
    cur.close()
    conn.close()
