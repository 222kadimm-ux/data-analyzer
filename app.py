import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
import io
import json
import uuid
import sentry_sdk
import gspread
import extra_streamlit_components as stx
from google.oauth2.service_account import Credentials
from sqlalchemy import create_engine
from database import init_db, save_file, get_files, delete_file, get_db_connection
from auth import create_user, verify_user, login_user, logout_user
from ai_engine import ask_ai_about_data, generate_sql_from_question

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
# 2. إدارة الكوكيز (الحفظ التلقائي)
# ==========================================
cookie_manager = stx.CookieManager(key="cookie_manager")

# إنشاء أو جلب معرّف المستخدم المجهول (UUID)
if 'anon_uuid' not in st.session_state:
    saved_uuid = cookie_manager.get(cookie="anon_uuid")
    if saved_uuid:
        st.session_state.anon_uuid = saved_uuid
    else:
        new_uuid = str(uuid.uuid4())
        cookie_manager.set("anon_uuid", new_uuid)
        st.session_state.anon_uuid = new_uuid

# تحديد هوية المستخدم الحالي (مسجل أو مجهول)
current_user = st.session_state.user_email if st.session_state.get('logged_in') else st.session_state.anon_uuid

# ==========================================
# 3. الدوال المساعدة
# ==========================================
def load_from_gsheets(sheet_url):
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        data = client.open_by_url(sheet_url).sheet1.get_all_records()
        return pl.from_pandas(pd.DataFrame(data)) if data else None
    except: return None

def load_from_sql(db_url, table_name, limit=10000):
    try:
        engine = create_engine(db_url)
        df_pd = pd.read_sql(f"SELECT * FROM {table_name} LIMIT {limit};", engine)
        return pl.from_pandas(df_pd)
    except: return None

def delete_my_account(email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user_files WHERE user_email = %s", (email,))
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        return True
    except: return False
    finally: cur.close(); conn.close()

# ==========================================
# 4. تهيئة الجلسة
# ==========================================
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

if 'df' not in st.session_state: st.session_state.df = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'show_privacy' not in st.session_state: st.session_state.show_privacy = False

# ==========================================
# 5. القائمة الجانبية
# ==========================================
st.sidebar.title("الملف الشخصي")

if not st.session_state.logged_in:
    st.sidebar.info("أنت تستخدم التطبيق كزائر. عملك محفوظ تلقائياً على هذا الجهاز.")
    with st.sidebar.expander("🔑 تسجيل الدخول (اختياري)"):
        login_email = st.text_input("البريد", key="l_email")
        login_pass = st.text_input("كلمة المرور", type="password", key="l_pass")
        if st.button("دخول"):
            if verify_user(login_email, login_pass):
                login_user(login_email); st.rerun()
            else: st.error("بيانات خاطئة.")
        
        new_email = st.text_input("بريد جديد", key="n_email")
        new_pass = st.text_input("كلمة مرور جديدة", type="password", key="n_pass")
        if st.button("إنشاء حساب"):
            if len(new_pass) < 6: st.warning("قصيرة.")
            elif create_user(new_email, new_pass): st.success("✅"); st.rerun()
else:
    st.sidebar.write(f"👤 {st.session_state.user_email}")
    if st.sidebar.button("تسجيل الخروج"): logout_user()

st.sidebar.divider()
st.sidebar.subheader("🗂️ عملك السابق")
# جلب الملفات بناءً على الهوية (سواء UUID أو بريد)
files = get_files(current_user)
if not files:
    st.sidebar.caption("لا توجد ملفات محفوظة بعد.")
for f in files:
    col1, col2 = st.sidebar.columns([4, 1])
    if col1.button(f"{f[1]}", key=f"load_{f[0]}"):
        data = json.loads(f[2]) if isinstance(f[2], str) else f[2]
        st.session_state.df = pl.from_pandas(pd.DataFrame(data)); st.rerun()
    if col2.button("🗑️", key=f"del_{f[0]}"):
        delete_file(f[0], current_user); st.rerun()

st.sidebar.divider()
if st.sidebar.button("📜 سياسة الخصوصية"): st.session_state.show_privacy = True; st.rerun()

if st.session_state.show_privacy:
    st.title("📜 سياسة الخصوصية")
    st.markdown("- **لا PII:** لا نطلب اسمك.\n- **كوكيز:** نستخدم UUID مجهول لحفظ عملك.\n- **حذف البيانات:** يمكنك حذف ملفاتك من القائمة.")
    if st.button("العودة"): st.session_state.show_privacy = False; st.rerun()
    st.stop()

# ==========================================
# 6. الواجهة الرئيسية
# ==========================================
st.title("🏭 محلل بيانات المصانع (OEE & AI)")

if st.button("📊 تجربة سريعة"):
    demo_data = {
        'Machine': ['Line 1', 'Line 2', 'Line 1', 'Line 3', 'Line 2', 'Line 1'],
        'Planned_Time_Mins': [480, 480, 480, 480, 480, 480],
        'Downtime_Mins': [30, 10, 120, 60, 15, 45],
        'Ideal_Cycle_Time_Sec': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0],
        'Total_Count': [1500, 2500, 1200, 6000, 2200, 1400],
        'Good_Count': [1450, 2480, 1100, 5700, 2190, 1320],
        'Downtime_Reason': ['Maintenance', 'Setup', 'Breakdown', 'Breakdown', 'Setup', 'Material Shortage']
    }
    df = pl.from_pandas(pd.DataFrame(demo_data))
    st.session_state.df = df
    save_file(current_user, "Demo_Data", df.to_pandas()) # حفظ تلقائي
    st.rerun()

st.divider()

tab_upload, tab_dashboard, tab_oee, tab_ai, tab_sql = st.tabs(["1️⃣ رفع البيانات", "2️⃣ لوحة التحكم", "3️⃣ OEE", "4️⃣ المساعد الذكي", "5️⃣ اسأل SQL"])

with tab_upload:
    option = st.radio("اختر طريقة الرفع:", ["رفع ملف", "Google Sheets", "قاعدة بيانات SQL"])
    
    if option == "رفع ملف":
        uploaded_file = st.file_uploader("اختر ملف Excel أو CSV", type=["xlsx", "csv"])
        if uploaded_file:
            if uploaded_file.size > 100 * 1024 * 1024: st.error("🚫 الحد 100MB."); st.stop()
            with st.spinner("جارٍ التحليل..."):
                try:
                    df = pl.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pl.read_excel(uploaded_file)
                    df = df.drop_nulls().unique()
                    st.session_state.df = df
                    
                    # الحفظ التلقائي للمجهول
                    save_file(current_user, uploaded_file.name, df.head(5000).to_pandas() if df.height > 5000 else df.to_pandas())
                    
                    st.success(f"✅ تم الرفع! ({df.height:,} صف)")
                except Exception as e: st.error(f"❌ خطأ: {e}")

    elif option == "Google Sheets":
        gs_url = st.text_input("رابط Google Sheet:")
        if st.button("سحب"):
            if gs_url:
                df = load_from_gsheets(gs_url)
                if df is not None: 
                    st.session_state.df = df
                    save_file(current_user, "Google_Sheets_Data", df.head(5000).to_pandas())
                    st.success("✅ تم!")
                else: st.error("❌ فشل الاتصال.")

    elif option == "قاعدة بيانات SQL":
        db_url = st.text_input("رابط قاعدة البيانات (postgresql://...)", type="password")
        table_name = st.text_input("اسم الجدول:")
        if st.button("سحب"):
            if db_url and table_name:
                with st.spinner("جارٍ السحب..."):
                    df = load_from_sql(db_url, table_name)
                    if df is not None: 
                        st.session_state.df = df
                        save_file(current_user, "SQL_Data", df.to_pandas())
                        st.success("✅ تم!")
                    else: st.error("❌ فشل الاتصال.")

with tab_dashboard:
    if st.session_state.df is None: st.info("⚠️ ارفع البيانات أولاً.")
    else:
        df_pl = st.session_state.df
        df = df_pl.to_pandas()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
        
        if numeric_cols and cat_cols:
            c1, c2, c3 = st.columns(3)
            c1.metric("السجلات", f"{df_pl.height:,}")
            c2.metric("الإجمالي", f"{df_pl[numeric_cols[0]].sum():,.0f}")
            best_item = df_pl.group_by(cat_cols[0]).agg(pl.col(numeric_cols[0]).sum()).sort(numeric_cols[0], descending=True).head(1)[cat_cols[0]][0]
            c3.metric("الأعلى", str(best_item))
            st.plotly_chart(px.bar(df.groupby(cat_cols[0])[numeric_cols[0]].sum().reset_index(), x=cat_cols[0], y=numeric_cols[0], color=numeric_cols[0]), use_container_width=True)

            st.divider()
            c1, c2 = st.columns(2)
            c1.download_button("CSV", df.to_csv(index=False).encode('utf-8-sig'), "data.csv")
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer: df.to_excel(writer, index=False)
            c2.download_button("Excel", excel_buffer.getvalue(), "data.xlsx")

with tab_oee:
    if st.session_state.df is None: st.info("⚠️ ارفع البيانات أولاً.")
    else:
        df = st.session_state.df.to_pandas()
        required_cols = ['Planned_Time_Mins', 'Downtime_Mins', 'Ideal_Cycle_Time_Sec', 'Total_Count', 'Good_Count']
        
        if all(col in df.columns for col in required_cols):
            df['Run_Time_Mins'] = df['Planned_Time_Mins'] - df['Downtime_Mins']
            df['Availability'] = df['Run_Time_Mins'] / df['Planned_Time_Mins']
            df['Ideal_Time_Mins'] = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']) / 60
            df['Performance'] = df['Ideal_Time_Mins'] / df['Run_Time_Mins']
            df['Quality'] = df['Good_Count'] / df['Total_Count']
            df['OEE'] = df['Availability'] * df['Performance'] * df['Quality']
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("الإتاحة", f"{df['Availability'].mean()*100:.1f}%")
            c2.metric("الأداء", f"{df['Performance'].mean()*100:.1f}%")
            c3.metric("الجودة", f"{df['Quality'].mean()*100:.1f}%")
            c4.metric("OEE الإجمالي", f"{df['OEE'].mean()*100:.1f}%")
            
            if 'Downtime_Reason' in df.columns:
                st.plotly_chart(px.bar(df.groupby('Downtime_Reason')['Downtime_Mins'].sum().reset_index().sort_values('Downtime_Mins', ascending=False), x='Downtime_Reason', y='Downtime_Mins', color='Downtime_Mins'), use_container_width=True)
        else:
            st.warning("⚠️ لبيانات OEE، يجب أن يحتوي ملفك على:")
            st.code(", ".join(required_cols))

with tab_ai:
    if st.session_state.df is None: st.info("⚠️ ارفع البيانات أولاً.")
    else:
        if st.button("📝 تقرير تلقائي"):
            with st.spinner("جاري التحليل..."):
                st.info(ask_ai_about_data("أعطني تقريراً تحليلياً شاملاً وأهم 3 توصيات.", st.session_state.df))
        
        question = st.text_input("اسأل:")
        if st.button("إرسال"):
            if question: st.success(ask_ai_about_data(question, st.session_state.df))

with tab_sql:
    sql_db_url = st.text_input("1. رابط قاعدة البيانات (postgresql://...)", type="password", key="sql_db")
    sql_table = st.text_input("2. اسم الجدول:", key="sql_table")
    sql_question = st.text_input("3. سؤالك (مثلاً: كم عدد المنتجات المعيبة؟)", key="sql_q")
    
    if st.button("توليد وتنفيذ الاستعلام"):
        if sql_db_url and sql_table and sql_question:
            with st.spinner("الذكاء الاصطناعي يكتب الاستعلام..."):
                generated_sql, error = generate_sql_from_question(sql_question, sql_table)
                
                if error: st.error(f"حدث خطأ: {error}")
                else:
                    st.code(generated_sql, language="sql")
                    try:
                        engine = create_engine(sql_db_url)
                        result_df = pd.read_sql(generated_sql, engine)
                        st.success(f"✅ تم التنفيذ! ({len(result_df)} نتيجة)")
                        st.dataframe(result_df)
                    except Exception as e:
                        st.error(f"❌ فشل التنفيذ: {e}")
        else:
            st.warning("يرجى ملء جميع الحقول.")
