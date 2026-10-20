import streamlit as st
import psycopg2

DB_URL = "postgresql://neondb_owner:npg_qVub1K6DCvcz@ep-purple-mud-b5sns22j-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

st.set_page_config(page_title="Admin Panel", page_icon="👑")
st.title("👑 لوحة تحكم المدير")

# طلب كلمة المرور (يمكنك تغييرها إلى كلمة سرية جداً)
admin_password = st.text_input("أدخل كلمة مرور المدير", type="password")

if admin_password == st.secrets["ADMIN_SECRET"]:
    st.success("مرحباً أيها المدير.")
    
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total_users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM user_files")
    total_files = cur.fetchone()[0]
    
    c1, c2 = st.columns(2)
    c1.metric("إجمالي المستخدمين", total_users)
    c2.metric("إجمالي الملفات المرفوعة", total_files)
    
    st.divider()
    st.subheader("آخر الأحداث (Audit Logs)")
    cur.execute("SELECT user_email, action, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10")
    logs = cur.fetchall()
    for log in logs:
        st.text(f"👤 {log[0]} | 📝 {log[1]} | 🕒 {log[2]}")
        
    cur.close()
    conn.close()
elif admin_password:
    st.error("كلمة مرور خاطئة.")