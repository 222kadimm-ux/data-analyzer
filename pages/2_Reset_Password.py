import streamlit as st
import psycopg2
import bcrypt

DB_URL = "postgresql://neondb_owner:npg_qVub1K6DCvcz@ep-purple-mud-b5sns22j-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

st.set_page_config(page_title="Reset Password", page_icon="🔑")
st.title("🔑 استعادة كلمة المرور")

email = st.text_input("البريد الإلكتروني")
security_answer = st.text_input("سؤال الأمان (نفس الإجابة التي وضعتها عند التسجيل)")
new_password = st.text_input("كلمة المرور الجديدة", type="password")

if st.button("تغيير كلمة المرور"):
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("SELECT security_answer FROM users WHERE email = %s", (email,))
    result = cur.fetchone()
    
    if result and result[0] == security_answer:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed, email))
        conn.commit()
        st.success("✅ تم تغيير كلمة المرور بنجاح! يمكنك العودة لتسجيل الدخول.")
    else:
        st.error("البريد الإلكتروني أو إجابة سؤال الأمان غير صحيحة.")
    
    cur.close()
    conn.close()