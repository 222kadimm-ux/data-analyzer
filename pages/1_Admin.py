import streamlit as st
import psycopg2

DB_URL = "postgresql://neondb_owner:npg_qVub1K6DCvcz@ep-purple-mud-b5sns22j-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
ADMIN_PASS = "MySecretAdminPassword123" # ⚠️ غير هذه الكلمة إلى كلمة سرية جداً

st.set_page_config(page_title="Admin Panel", page_icon="👑")
st.title("👑 لوحة تحكم المدير")

password = st.text_input("أدخل كلمة مرور المدير", type="password")

if password == ADMIN_PASS:
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM user_files")
    total_files = cur.fetchone()[0]
    
    st.success("مرحباً بك أيها المدير.")
    c1, c2 = st.columns(2)
    c1.metric("إجمالي المستخدمين", total_users)
    c2.metric("إجمالي الملفات المرفوعة", total_files)
    
    st.divider()
    st.subheader("أحدث المستخدمين")
    cur.execute("SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 5")
    users = cur.fetchall()
    for u in users:
        st.write(f"- {u[0]} (تاريخ التسجيل: {u[1].strftime('%Y-%m-%d')})")
        
    cur.close()
    conn.close()
elif password:
    st.error("كلمة مرور خاطئة.")