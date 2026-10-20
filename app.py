import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import bcrypt
import json
import io

# --- إعدادات قاعدة البيانات (Neon) ---
DB_URL = "postgresql://neondb_owner:npg_qVub1K6DCvcz@ep-purple-mud-b5sns22j-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

st.set_page_config(page_title="Pro Data Analyzer", page_icon="💼", layout="wide")

# --- دوال قاعدة البيانات ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

def create_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cur.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        return False
    finally:
        cur.close()
        conn.close()

def verify_user(email, password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8'))
    return False

def save_file_to_db(email, filename, df):
    conn = get_db_connection()
    cur = conn.cursor()
    json_data = df.to_json(orient='records')
    try:
        cur.execute(
            "INSERT INTO user_files (user_email, file_name, file_data) VALUES (%s, %s, %s)",
            (email, filename, json_data)
        )
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def get_user_files(email):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, file_name, file_data, created_at FROM user_files WHERE user_email = %s ORDER BY created_at DESC", (email,))
    files = cur.fetchall()
    cur.close()
    conn.close()
    return files

# --- إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'df' not in st.session_state:
    st.session_state.df = None

# --- شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 مرحباً بك في منصة تحليل البيانات")
    
    tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب جديد"])
    
    with tab1:
        login_email = st.text_input("البريد الإلكتروني", key="login_email")
        login_pass = st.text_input("كلمة المرور", type="password", key="login_pass")
        if st.button("دخول", type="primary"):
            if verify_user(login_email, login_pass):
                st.session_state.logged_in = True
                st.session_state.user_email = login_email
                st.rerun()
            else:
                st.error("البريد الإلكتروني أو كلمة المرور غير صحيحة.")
                
    with tab2:
        new_email = st.text_input("البريد الإلكتروني الجديد", key="new_email")
        new_pass = st.text_input("كلمة المرور الجديدة", type="password", key="new_pass")
        if st.button("إنشاء الحساب"):
            if len(new_pass) < 6:
                st.warning("كلمة المرور يجب أن تكون 6 أحرف على الأقل.")
            elif create_user(new_email, new_pass):
                st.success("تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
            else:
                st.error("هذا البريد الإلكتروني مسجل مسبقاً.")
    st.stop()

# --- التطبيق بعد تسجيل الدخول ---
st.sidebar.write(f"👤 {st.session_state.user_email}")

# الترجمة
lang = st.sidebar.radio("Language / اللغة", ["العربية", "English"])
t = {
    "العربية": {
        "title": "💼 منصة تحليل البيانات الاحترافية",
        "subtitle": "ارفع ملفك، وقم بتحليله فوراً.",
        "upload": "📂 رفع ملف جديد (Excel/CSV)",
        "history": "🗂️ ملفاتي السابقة",
        "export": "📥 تحميل التقرير (CSV)",
        "clear": "🗑️ مسح الشاشة",
        "stats": "📊 لوحة القيادة",
        "total_ops": "إجمالي العمليات",
        "total_val": "إجمالي القيمة",
        "best_item": "أفضل عنصر",
        "charts": "📈 التحليل البياني",
        "col_x": "التصنيف",
        "col_y": "القيمة",
        "bar": "المنتجات الأكثر ربحاً",
        "pie": "توزيع الحصص",
        "data": "📋 البيانات الخام"
    },
    "English": {
        "title": "💼 Pro Data Analytics Platform",
        "subtitle": "Upload your file and analyze instantly.",
        "upload": "📂 Upload New File (Excel/CSV)",
        "history": "🗂️ My Previous Files",
        "export": "📥 Export Report (CSV)",
        "clear": "🗑️ Clear Screen",
        "stats": "📊 Dashboard",
        "total_ops": "Total Operations",
        "total_val": "Total Value",
        "best_item": "Top Item",
        "charts": "📈 Charts",
        "col_x": "Category",
        "col_y": "Value",
        "bar": "Most Profitable Items",
        "pie": "Share Distribution",
        "data": "📋 Raw Data"
    }
}[lang]

# --- القائمة الجانبية: سجل الملفات ---
st.sidebar.divider()
st.sidebar.subheader(t["history"])
user_files = get_user_files(st.session_state.user_email)

if user_files:
    file_options = {f"{f[1]} ({f[3].strftime('%Y-%m-%d')})": f[2] for f in user_files}
    selected_file_name = st.sidebar.selectbox("اختر ملفاً لتحميله:", ["-- اختر --"] + list(file_options.keys()))
    
    if selected_file_name != "-- اختر --":
        if st.sidebar.button("تحميل الملف المحدد"):
            json_data = file_options[selected_file_name]
            # هذا هو السطر الذي تم إصلاحه
            st.session_state.df = pd.DataFrame(json.loads(json_data))
            st.rerun()
else:
    st.sidebar.info("لا توجد ملفات سابقة.")

if st.sidebar.button(t["clear"]):
    st.session_state.df = None
    st.rerun()

if st.sidebar.button("تسجيل الخروج"):
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.df = None
    st.rerun()

# --- واجهة التطبيق الرئيسية ---
st.title(t["title"])
st.markdown(f"*{t['subtitle']}*")

uploaded_file = st.file_uploader(t["upload"], type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # حفظ الملف في قاعدة البيانات
        if save_file_to_db(st.session_state.user_email, uploaded_file.name, df):
            st.session_state.df = df
            st.success(f"✅ تم رفع وحفظ {uploaded_file.name} بنجاح!")
        else:
            st.warning("تم التحليل ولكن تعذر حفظ الملف في السجل.")
            
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.df is not None:
    df = st.session_state.df
    
    # أزرار التصدير
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button(label=t["export"], data=csv, file_name='report.csv', mime='text/csv')
    
    st.divider()
    
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()

    if numeric_cols and categorical_cols:
        st.subheader(t["stats"])
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(t["total_ops"], len(df))
        with c2:
            st.metric(f"{t['total_val']} ({numeric_cols[0]})", f"{df[numeric_cols[0]].sum():,.0f}")
        with c3:
            best = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().idxmax()
            st.metric(f"{t['best_item']} ({categorical_cols[0]})", best)

        st.subheader(t["charts"])
        c1, c2 = st.columns(2)
        with c1:
            col_x = st.selectbox(t["col_x"], categorical_cols)
        with c2:
            col_y = st.selectbox(t["col_y"], numeric_cols)

        chart_data = df.groupby(col_x)[col_y].sum().reset_index().sort_values(by=col_y, ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            fig_bar = px.bar(chart_data, x=col_x, y=col_y, color=col_y, color_continuous_scale='Teal')
            fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_bar, use_container_width=True)
        with c2:
            fig_pie = px.pie(chart_data, names=col_x, values=col_y, hole=0.4)
            fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_pie, use_container_width=True)

        with st.expander(t["data"]):
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ الملف لا يحتوي على بيانات كافية.")