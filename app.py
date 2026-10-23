import streamlit as st
import pandas as pd
import plotly.express as px
import io
import json
import time
import sentry_sdk
from database import init_db, save_file, get_files, delete_file, get_db_connection
from auth import create_user, verify_user, login_user, logout_user
from ai_engine import ask_ai_about_data

# ==========================================
# 1. إعدادات الصفحة والمراقبة
# ==========================================
st.set_page_config(page_title="Pro Data Analyzer", page_icon="💼", layout="wide")

try:
    sentry_sdk.init(dsn=st.secrets.get("SENTRY_DSN", ""), traces_sample_rate=1.0)
except Exception:
    pass

# تصميم مريح للعين
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    div[data-testid="stMetric"] { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4257; }
    .stButton > button { border-radius: 8px; font-weight: bold; background-color: #4CAF50; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { padding: 10px 20px; border-radius: 10px; color: #ffffff; }
    .stTabs [aria-selected="true"] { background-color: #1e2130; }
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. تهيئة الجلسة (بدون تسجيل إجباري)
# ==========================================
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

if 'df' not in st.session_state: st.session_state.df = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = None

# ==========================================
# 3. القائمة الجانبية (اختيارية)
# ==========================================
st.sidebar.title("الملف الشخصي (اختياري)")

if not st.session_state.logged_in:
    st.sidebar.write("سجل الدخول لحفظ ملفاتك.")
    with st.sidebar.expander("🔑 تسجيل الدخول / إنشاء حساب"):
        login_email = st.text_input("البريد الإلكتروني", key="l_email")
        login_pass = st.text_input("كلمة المرور", type="password", key="l_pass")
        if st.button("دخول"):
            if verify_user(login_email, login_pass):
                login_user(login_email)
                st.rerun()
            else:
                st.error("بيانات خاطئة.")
        
        st.write("---")
        new_email = st.text_input("بريد جديد", key="n_email")
        new_pass = st.text_input("كلمة مرور جديدة", type="password", key="n_pass")
        if st.button("إنشاء حساب"):
            if len(new_pass) < 6:
                st.warning("كلمة المرور قصيرة.")
            elif create_user(new_email, new_pass):
                st.success("✅ تم إنشاء الحساب!")
                st.rerun()
            else:
                st.error("البريد مسجل مسبقاً.")
else:
    st.sidebar.write(f"👤 {st.session_state.user_email}")
    if st.sidebar.button("تسجيل الخروج"):
        logout_user()
    
    st.sidebar.divider()
    st.sidebar.subheader("🗂️ ملفاتي السابقة")
    files = get_files(st.session_state.user_email)
    for f in files:
        col1, col2 = st.sidebar.columns([4, 1])
        if col1.button(f"{f[1]}", key=f"load_{f[0]}"):
            try:
                data = f[2]
                if isinstance(data, str): data = json.loads(data)
                st.session_state.df = pd.DataFrame(data)
                st.rerun()
            except: pass
        if col2.button("🗑️", key=f"del_{f[0]}"):
            delete_file(f[0], st.session_state.user_email)
            st.rerun()

# ==========================================
# 4. الواجهة الرئيسية (متاحة للجميع فوراً)
# ==========================================
st.title("💼 محلل البيانات الاحترافي (AI Data Analyst)")
st.write("ارفع ملفك مباشرة، أو استخدم زر البيانات التجريبية للتجربة الفورية.")

# زر البيانات التجريبية
if st.button("📊 تجربة سريعة (بيانات تجريبية)"):
    demo_data = {
        'Product': ['Shirt', 'Pants', 'Shoes', 'Jacket', 'Shirt', 'Shoes'],
        'Amount': [1500, 2500, 4000, 6000, 1500, 4000],
        'Month': ['Jan', 'Jan', 'Feb', 'Feb', 'Mar', 'Mar']
    }
    st.session_state.df = pd.DataFrame(demo_data)
    st.rerun()

st.divider()

tab_upload, tab_dashboard, tab_ai = st.tabs(["1️⃣ رفع البيانات", "2️⃣ لوحة التحكم الإحصائية", "3️⃣ المساعد الذكي (AI)"])

with tab_upload:
    uploaded_file = st.file_uploader("اختر ملف Excel أو CSV", type=["xlsx", "csv"])
    if uploaded_file:
        with st.spinner("جارٍ تحليل الملف..."):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                df = df.dropna().drop_duplicates()
                st.session_state.df = df
                if st.session_state.logged_in:
                    save_file(st.session_state.user_email, uploaded_file.name, df)
                st.success("✅ تم رفع الملف بنجاح! اذهب للتبويب الثاني.")
            except Exception as e:
                st.error(f"خطأ: {e}")

with tab_dashboard:
    if st.session_state.df is None:
        st.info("⚠️ يرجى رفع ملف أولاً (أو استخدام البيانات التجريبية).")
    else:
        df = st.session_state.df
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        if numeric_cols and cat_cols:
            st.subheader("📊 الإحصائيات الأساسية")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("إجمالي العمليات", len(df))
            c2.metric(f"الإجمالي ({numeric_cols[0]})", f"{df[numeric_cols[0]].sum():,.0f}")
            best_item = df.groupby(cat_cols[0])[numeric_cols[0]].sum().idxmax()
            c3.metric("أفضل منتج", best_item)
            c4.metric("متوسط القيمة", f"{df[numeric_cols[0]].mean():,.1f}")

            st.divider()
            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("📈 توزيع الفئات")
                chart_data = df.groupby(cat_cols[0])[numeric_cols[0]].sum().reset_index()
                st.plotly_chart(px.bar(chart_data, x=cat_cols[0], y=numeric_cols[0], color=numeric_cols[0]), use_container_width=True)
            
            with col_right:
                st.subheader("🔗 مصفوفة الارتباطات")
                if len(numeric_cols) > 1:
                    corr = df[numeric_cols].corr()
                    fig = px.imshow(corr, text_auto=True, aspect="auto", color_continuous_scale='RdBu')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("تحتاج إلى عمودين رقميين على الأقل.")
            
            st.divider()
            st.subheader("📥 تصدير النتائج")
            c1, c2 = st.columns(2)
            c1.download_button("تحميل كـ CSV", df.to_csv(index=False).encode('utf-8-sig'), "data.csv", "text/csv")
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            c2.download_button("تحميل كـ Excel", excel_buffer.getvalue(), "data.xlsx")

with tab_ai:
    if st.session_state.df is None:
        st.info("⚠️ يرجى رفع ملف أولاً.")
    else:
        st.subheader("💬 المساعد الذكي (AI Analyst)")
        if st.button("📝 توليد تقرير تحليلي تلقائي"):
            with st.spinner("الذكاء الاصطناعي يحلل البيانات..."):
                report = ask_ai_about_data("أعطني تقريراً تحليلياً شاملاً وأهم 3 توصيات.", st.session_state.df)
                st.info(report)
        
        st.divider()
        question = st.text_input("اسأل سؤالاً محدداً:")
        if st.button("إرسال السؤال"):
            if question:
                with st.spinner("جاري التحليل..."):
                    answer = ask_ai_about_data(question, st.session_state.df)
                    st.success(answer)
