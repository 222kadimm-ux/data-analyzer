import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
import io
import json
import time
import sentry_sdk
import gspread
from google.oauth2.service_account import Credentials
from sqlalchemy import create_engine
from database import init_db, save_file, get_files, delete_file, get_db_connection
from auth import create_user, verify_user, login_user, logout_user
from ai_engine import ask_ai_about_data

# ==========================================
# 1. إعدادات الصفحة والمراقبة
# ==========================================
st.set_page_config(page_title="Pro Data Analyzer", page_icon="🏭", layout="wide")

try:
    sentry_sdk.init(dsn=st.secrets.get("SENTRY_DSN", ""), traces_sample_rate=1.0, send_default_pii=False)
except Exception:
    pass

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
# 2. دوال الاتصال (Google Sheets & SQL)
# ==========================================
def load_from_gsheets(sheet_url):
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(sheet_url).sheet1
        data = sheet.get_all_records()
        return pl.from_pandas(pd.DataFrame(data)) if data else None
    except:
        return None

def load_from_sql(db_url, table_name, limit=10000):
    try:
        engine = create_engine(db_url)
        query = f"SELECT * FROM {table_name} LIMIT {limit};"
        df_pd = pd.read_sql(query, engine)
        return pl.from_pandas(df_pd)
    except Exception as e:
        return None

# ==========================================
# 3. تهيئة الجلسة
# ==========================================
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

if 'df' not in st.session_state: st.session_state.df = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'show_privacy' not in st.session_state: st.session_state.show_privacy = False

def delete_my_account(email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user_files WHERE user_email = %s", (email,))
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        return True
    except:
        return False
    finally:
        cur.close()
        conn.close()

# ==========================================
# 4. القائمة الجانبية (نفس الكود السابق)
# ==========================================
st.sidebar.title("الملف الشخصي (اختياري)")

if not st.session_state.logged_in:
    with st.sidebar.expander("🔑 تسجيل الدخول"):
        login_email = st.text_input("البريد", key="l_email")
        login_pass = st.text_input("كلمة المرور", type="password", key="l_pass")
        if st.button("دخول"):
            if verify_user(login_email, login_pass):
                login_user(login_email)
                st.rerun()
            else:
                st.error("بيانات خاطئة.")
        
        new_email = st.text_input("بريد جديد", key="n_email")
        new_pass = st.text_input("كلمة مرور جديدة", type="password", key="n_pass")
        if st.button("إنشاء حساب"):
            if len(new_pass) < 6:
                st.warning("كلمة المرور قصيرة.")
            elif create_user(new_email, new_pass):
                st.success("✅ تم إنشاء الحساب!")
                st.rerun()
            else:
                st.error("مسجل مسبقاً.")
else:
    st.sidebar.write(f"👤 {st.session_state.user_email}")
    if st.sidebar.button("تسجيل الخروج"):
        logout_user()
    st.sidebar.divider()
    st.sidebar.subheader("🗂️ تقاريري السابقة")
    for f in get_files(st.session_state.user_email):
        col1, col2 = st.sidebar.columns([4, 1])
        if col1.button(f"{f[1]}", key=f"load_{f[0]}"):
            data = json.loads(f[2]) if isinstance(f[2], str) else f[2]
            st.session_state.df = pl.from_pandas(pd.DataFrame(data))
            st.rerun()
        if col2.button("🗑️", key=f"del_{f[0]}"):
            delete_file(f[0], st.session_state.user_email)
            st.rerun()
    
    with st.sidebar.expander("⚙️ إدارة الحساب"):
        if st.button("🗑️ حذف حسابي"):
            if delete_my_account(st.session_state.user_email):
                st.success("تم الحذف.")
                logout_user()

st.sidebar.divider()
if st.sidebar.button("📜 سياسة الخصوصية"):
    st.session_state.show_privacy = True
    st.rerun()

if st.session_state.show_privacy:
    st.title("📜 سياسة الخصوصية")
    st.markdown("""
    - **لا نجمع بيانات شخصية (PII):** لا نطلب اسمك أو رقم هاتفك.
    - **الكوكيز:** نستخدم كوكيز تقني فقط لحفظ الجلسة.
    - **مدة الاحتفاظ:** يتم حذف البيانات المؤقتة تلقائياً بعد 30 يوماً.
    - **حق المسح:** يمكنك حذف حسابك وبياناتك في أي وقت.
    - **الذكاء الاصطناعي:** نرسل ملخص البيانات فقط (وليس الملف كاملاً) إلى OpenRouter.
    """)
    if st.button("العودة للتطبيق"):
        st.session_state.show_privacy = False
        st.rerun()
    st.stop()

# ==========================================
# 5. الواجهة الرئيسية
# ==========================================
st.title("🏭 محلل بيانات المصانع (OEE & AI)")
st.write("ارفع ملفك، أو اتصل بقاعدة بيانات مصنعك مباشرة، للحصول على تقارير ذكية.")

if st.button("📊 تجربة سريعة (بيانات تصنيع تجريبية)"):
    demo_data = {
        'Machine': ['Line 1', 'Line 2', 'Line 1', 'Line 3', 'Line 2', 'Line 1'],
        'Output': [1500, 2500, 1200, 6000, 2200, 1400],
        'Defects': [50, 20, 100, 300, 10, 80],
        'Downtime_Mins': [30, 10, 120, 60, 15, 45]
    }
    st.session_state.df = pl.from_pandas(pd.DataFrame(demo_data))
    st.rerun()

st.divider()

tab_upload, tab_dashboard, tab_ai = st.tabs(["1️⃣ رفع البيانات", "2️⃣ لوحة التحكم الإحصائية", "3️⃣ المساعد الذكي (AI)"])

with tab_upload:
    option = st.radio("اختر طريقة رفع البيانات:", ["رفع ملف", "Google Sheets", "قاعدة بيانات SQL"])
    
    if option == "رفع ملف":
        uploaded_file = st.file_uploader("اختر ملف Excel أو CSV", type=["xlsx", "csv"])
        if uploaded_file:
            if uploaded_file.size > 100 * 1024 * 1024:
                st.error("🚫 الملف كبير جداً! الحد الأقصى 100 ميجابايت.")
                st.stop()
            with st.spinner("جارٍ التحليل..."):
                try:
                    df = pl.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pl.read_excel(uploaded_file)
                    st.session_state.df = df.drop_nulls().unique()
                    st.success(f"✅ تم الرفع! ({df.height:,} صف)")
                except Exception as e:
                    st.error(f"❌ خطأ في قراءة الملف: {e}")

    elif option == "Google Sheets":
        gs_url = st.text_input("أدخل رابط Google Sheet:")
        if st.button("سحب البيانات"):
            if gs_url:
                df = load_from_gsheets(gs_url)
                if df is not None:
                    st.session_state.df = df
                    st.success("✅ تم السحب!")
                else:
                    st.error("❌ فشل الاتصال. تأكد من الصلاحيات.")

    elif option == "قاعدة بيانات SQL":
        st.info("💡 (في الإنتاج، يتم الاتصال بقاعدة بيانات المصنع الخاصة بك)")
        db_url = st.text_input("رابط قاعدة البيانات (postgresql://user:pass@host/db)", type="password")
        table_name = st.text_input("اسم الجدول (مثلاً: production_log)")
        if st.button("سحب من قاعدة البيانات"):
            if db_url and table_name:
                with st.spinner("جارٍ السحب (حد 10,000 صف)..."):
                    df = load_from_sql(db_url, table_name)
                    if df is not None:
                        st.session_state.df = df
                        st.success("✅ تم السحب!")
                    else:
                        st.error("❌ فشل الاتصال بقاعدة البيانات. تأكد من الرابط.")

with tab_dashboard:
    if st.session_state.df is None:
        st.info("⚠️ يرجى رفع البيانات أولاً.")
    else:
        df_pl = st.session_state.df
        df = df_pl.to_pandas()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        if numeric_cols and cat_cols:
            st.subheader("📊 مؤشرات الأداء")
            c1, c2, c3 = st.columns(3)
            c1.metric("إجمالي السجلات", f"{df_pl.height:,}")
            c2.metric(f"الإجمالي ({numeric_cols[0]})", f"{df_pl[numeric_cols[0]].sum():,.0f}")
            best_item = df_pl.group_by(cat_cols[0]).agg(pl.col(numeric_cols[0]).sum()).sort(numeric_cols[0], descending=True).head(1)[cat_cols[0]][0]
            c3.metric("الأعلى إنتاجاً", str(best_item))

            st.divider()
            col_left, col_right = st.columns(2)
            with col_left:
                st.subheader("📈 توزيع الإنتاج")
                chart_data = df.groupby(cat_cols[0])[numeric_cols[0]].sum().reset_index()
                st.plotly_chart(px.bar(chart_data, x=cat_cols[0], y=numeric_cols[0], color=numeric_cols[0]), use_container_width=True)
            
            with col_right:
                st.subheader("🔗 الارتباطات")
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
        st.info("⚠️ يرجى رفع البيانات أولاً.")
    else:
        st.subheader("💬 المساعد الذكي (AI)")
        if st.button("📝 كتابة تقرير تلقائي"):
            with st.spinner("جاري التحليل..."):
                report = ask_ai_about_data("أعطني تقريراً تحليلياً شاملاً وأهم 3 توصيات.", st.session_state.df)
                st.info(report)
        
        st.divider()
        question = st.text_input("اسأل سؤالاً محدداً:")
        if st.button("إرسال السؤال"):
            if question:
                with st.spinner("جاري التحليل..."):
                    answer = ask_ai_about_data(question, st.session_state.df)
                    st.success(answer)
