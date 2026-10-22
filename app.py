import streamlit as st
import pandas as pd
import plotly.express as px
import io
import json
import time
import re
from database import init_db, save_file, get_files, delete_file
from auth import create_user, verify_user, login_user, logout_user
from ai_engine import ask_ai_about_data
from gsheets_integration import load_from_google_sheets

# تهيئة الإعدادات
st.set_page_config(page_title="Pro Data Analyzer", page_icon="💼", layout="wide")

# تصميم CSS
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    div[data-testid="stMetric"] { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4257; }
    .stButton > button { border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# تهيئة قاعدة البيانات مرة واحدة
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

# إدارة الحالة
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'df' not in st.session_state: st.session_state.df = None

# ==========================================
# شاشة تسجيل الدخول
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 مرحباً بك في منصة تحليل البيانات")
    
    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب جديد"])
    
    with tab1:
        if 'login_attempts' not in st.session_state: st.session_state.login_attempts = 0
        if 'last_attempt_time' not in st.session_state: st.session_state.last_attempt_time = 0
        
        if st.session_state.login_attempts >= 5:
            if time.time() - st.session_state.last_attempt_time < 60:
                st.error("🚫 تم حظرك مؤقتاً. انتظر دقيقة.")
                st.stop()
            else:
                st.session_state.login_attempts = 0
                
        login_email = st.text_input("البريد الإلكتروني", key="l_email")
        login_pass = st.text_input("كلمة المرور", type="password", key="l_pass")
        
        if st.button("دخول", type="primary"):
            if verify_user(login_email, login_pass):
                st.session_state.login_attempts = 0
                login_user(login_email)
                st.rerun()
            else:
                st.session_state.login_attempts += 1
                st.session_state.last_attempt_time = time.time()
                st.error(f"بيانات خاطئة. المحاولة {st.session_state.login_attempts}/5")
                
    with tab2:
        new_email = st.text_input("البريد الإلكتروني الجديد", key="n_email")
        new_pass = st.text_input("كلمة المرور (6 أحرف على الأقل)", type="password", key="n_pass")
        captcha = st.number_input("أثبت أنك إنسان: 3 + 7 = ؟", min_value=0)
        
        if st.button("إنشاء الحساب"):
            if len(new_pass) < 6:
                st.warning("كلمة المرور قصيرة جداً.")
            elif captcha != 10:
                st.error("إجابة التحقق خاطئة.")
            elif create_user(new_email, new_pass):
                st.success("✅ تم إنشاء الحساب! يمكنك الدخول الآن.")
            else:
                st.error("البريد مسجل مسبقاً.")
    st.stop()

# ==========================================
# التطبيق الرئيسي (بعد الدخول)
# ==========================================
st.sidebar.write(f"👤 {st.session_state.user_email}")

# زر لوحة المدير
if st.session_state.user_role == "admin":
    st.sidebar.page_link("pages/1_Admin_Panel.py", label="👑 لوحة المدير", icon="👑")

# --- ميزة Google Sheets ---
st.sidebar.divider()
st.sidebar.subheader("🔗 التكاملات الخارجية")
with st.sidebar.expander("📊 سحب من Google Sheets"):
    gs_url = st.text_input("أدخل رابط الشيت (URL):", key="gs_url")
    if st.button("سحب البيانات", key="gs_btn"):
        if gs_url:
            with st.spinner("جارٍ سحب البيانات..."):
                try:
                    # تحويل الرابط تلقائياً إلى صيغة CSV القابلة للقراءة
                    if "/edit" in gs_url:
                        csv_url = gs_url.split("/edit")[0] + "/export?format=csv"
                    else:
                        csv_url = gs_url
                    
                    df = pd.read_csv(csv_url)
                    
                    if df.empty:
                        st.sidebar.warning("الجدول فارغ!")
                    else:
                        st.session_state.df = df
                        save_file(st.session_state.user_email, "Google_Sheets_Data", df)
                        st.sidebar.success("✅ تم سحب البيانات بنجاح!")
                        st.rerun()
                except Exception as e:
                    st.sidebar.error(f"❌ فشل الاتصال. تأكد من أن الشيت مشارك للعامة (Anyone with the link).\n الخطأ: {e}")
        else:
            st.sidebar.warning("الرجاء إدخال الرابط.")

# سجل الملفات
st.sidebar.divider()
st.sidebar.subheader("🗂️ ملفاتي السابقة")
files = get_files(st.session_state.user_email)
for f in files:
    col1, col2 = st.sidebar.columns([4, 1])
    if col1.button(f"{f[1]}", key=f"load_{f[0]}"):
        try:
            # إصلاح خطأ قراءة الملفات القديمة
            data = f[2]
            if isinstance(data, str):
                data = json.loads(data)
            st.session_state.df = pd.DataFrame(data)
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"خطأ في قراءة الملف: {e}")
            
    if col2.button("🗑️", key=f"del_{f[0]}"):
        delete_file(f[0], st.session_state.user_email)
        st.rerun()

if st.sidebar.button("تسجيل الخروج"):
    logout_user()

# ==========================================
# تحليل البيانات
# ==========================================
st.title("💼 منصة تحليل البيانات الاحترافية")
uploaded_file = st.file_uploader("📂 رفع ملف جديد (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    with st.spinner("جارٍ تحليل الملف..."):
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            df = df.dropna().drop_duplicates()
            
            if save_file(st.session_state.user_email, uploaded_file.name, df):
                st.session_state.df = df
                st.success(f"✅ تم رفع {uploaded_file.name} بنجاح")
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {e}")

if st.session_state.df is not None:
    df = st.session_state.df
    
    # إحصائيات
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    
    if numeric_cols and cat_cols:
        c1, c2, c3 = st.columns(3)
        c1.metric("إجمالي العمليات", len(df))
        c2.metric(f"الإجمالي ({numeric_cols[0]})", f"{df[numeric_cols[0]].sum():,.0f}")
        best_item = df.groupby(cat_cols[0])[numeric_cols[0]].sum().idxmax()
        c3.metric("أفضل منتج", best_item)
        
        # الرسوم البيانية
        st.subheader("📈 التحليل البياني")
        chart_data = df.groupby(cat_cols[0])[numeric_cols[0]].sum().reset_index()
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.bar(chart_data, x=cat_cols[0], y=numeric_cols[0], color=numeric_cols[0]), use_container_width=True)
        with c2:
            st.plotly_chart(px.pie(chart_data, names=cat_cols[0], values=numeric_cols[0]), use_container_width=True)
            
        # الذكاء الاصطناعي
        st.divider()
        st.subheader("💬 المحادثة مع البيانات (AI)")
        question = st.text_input("اسأل عن بياناتك (مثال: ما هو أفضل منتج؟)")
        if question:
            with st.spinner("AI يفكر..."):
                answer = ask_ai_about_data(question, df)
                st.success(answer)
                
        # تصدير
        st.divider()
        c1, c2 = st.columns(2)
        c1.download_button("📥 تحميل CSV", df.to_csv(index=False).encode('utf-8-sig'), "data.csv", "text/csv")
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        c2.download_button("📥 تحميل Excel", excel_buffer.getvalue(), "data.xlsx")
