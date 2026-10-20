import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import bcrypt
import json
from groq import Groq

# --- إعدادات قاعدة البيانات ---
DB_URL = "postgresql://neondb_owner:npg_qVub1K6DCvcz@ep-purple-mud-b5sns22j-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
ADMIN_PASS = "MySecretAdminPassword123"

st.set_page_config(page_title="Pro Data Analyzer", page_icon="💼", layout="wide")

# --- إعدادات الذكاء الاصطناعي (Groq) ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception as e:
    groq_client = None

# --- دوال قاعدة البيانات ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

def create_user(email, password, security_answer):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cur.execute("INSERT INTO users (email, password_hash, security_answer) VALUES (%s, %s, %s)", (email, hashed, security_answer))
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
    except Exception:
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

def delete_user_file(file_id, user_email):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM user_files WHERE id = %s AND user_email = %s", (file_id, user_email))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting file: {e}")
        return False
    finally:
        cur.close()
        conn.close()

# --- إدارة الجلسة ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'df' not in st.session_state:
    st.session_state.df = None
if 'show_reset' not in st.session_state:
    st.session_state.show_reset = False
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False

# --- شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 مرحباً بك في منصة تحليل البيانات")
    
    if st.session_state.show_reset:
        st.subheader("🔑 استعادة كلمة المرور")
        reset_email = st.text_input("البريد الإلكتروني")
        reset_answer = st.text_input("إجابة سؤال الأمان")
        new_pass = st.text_input("كلمة المرور الجديدة", type="password")
        if st.button("تغيير كلمة المرور"):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT security_answer FROM users WHERE email = %s", (reset_email,))
            result = cur.fetchone()
            if result and result[0] == reset_answer:
                hashed = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute("UPDATE users SET password_hash = %s WHERE email = %s", (hashed, reset_email))
                conn.commit()
                st.success("تم التغيير بنجاح! يمكنك العودة لتسجيل الدخول.")
                st.session_state.show_reset = False
                st.rerun()
            else:
                st.error("بيانات خاطئة.")
            cur.close()
            conn.close()
        if st.button("العودة"):
            st.session_state.show_reset = False
            st.rerun()
    else:
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
            
            if st.button("نسيت كلمة المرور؟"):
                st.session_state.show_reset = True
                st.rerun()
                    
        with tab2:
            new_email = st.text_input("البريد الإلكتروني الجديد", key="new_email")
            new_pass = st.text_input("كلمة المرور الجديدة", type="password", key="new_pass")
            security_q = st.text_input("سؤال الأمان (مثلاً: اسم مدينتك المفضلة؟)", key="security_q")
            if st.button("إنشاء الحساب"):
                if len(new_pass) < 6:
                    st.warning("كلمة المرور يجب أن تكون 6 أحرف على الأقل.")
                elif not security_q:
                    st.warning("الرجاء إدخال إجابة سؤال الأمان.")
                elif create_user(new_email, new_pass, security_q):
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
        "upload": "📂 رفع ملف جديد (Excel/CSV)",
        "history": "🗂️ ملفاتي السابقة",
        "export": "📥 تحميل التقرير (CSV)",
        "clear": "🗑️ مسح الشاشة",
        "stats": "📊 لوحة القيادة",
        "charts": "📈 التحليل البياني",
        "data": "📋 البيانات الخام",
        "insights": "🧠 التحليل الذكي",
        "demo": "📊 عرض بيانات تجريبية",
        "chat": "💬 المحادثة مع البيانات (AI)"
    },
    "English": {
        "title": "💼 Pro Data Analytics Platform",
        "upload": "📂 Upload New File (Excel/CSV)",
        "history": "🗂️ My Previous Files",
        "export": "📥 Export Report (CSV)",
        "clear": "🗑️ Clear Screen",
        "stats": "📊 Dashboard",
        "charts": "📈 Charts",
        "data": "📋 Raw Data",
        "insights": "🧠 Smart Insights",
        "demo": "📊 Show Demo Data",
        "chat": "💬 Chat with Data (AI)"
    }
}[lang]

# --- زر البيانات التجريبية ---
if st.sidebar.button(t["demo"]):
    demo_data = {
        'Product': ['Shirt', 'Pants', 'Shoes', 'Jacket', 'Shirt', 'Shoes'],
        'Amount': [1500, 2500, 4000, 6000, 1500, 4000],
        'Month': ['Jan', 'Jan', 'Feb', 'Feb', 'Mar', 'Mar']
    }
    st.session_state.df = pd.DataFrame(demo_data)
    st.rerun()

# --- القائمة الجانبية: سجل الملفات (مع ميزة الحذف) ---
st.sidebar.divider()
st.sidebar.subheader(t["history"])
user_files = get_user_files(st.session_state.user_email)
if user_files:
    for f in user_files:
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            if st.button(f"{f[1]} ({f[3].strftime('%Y-%m-%d')})", key=f"load_{f[0]}"):
                json_data = f[2]
                if isinstance(json_data, str):
                    st.session_state.df = pd.DataFrame(json.loads(json_data))
                else:
                    st.session_state.df = pd.DataFrame(json_data)
                st.rerun()
        with col2:
            if st.button("🗑️", key=f"del_{f[0]}"):
                if delete_user_file(f[0], st.session_state.user_email):
                    st.success("تم الحذف!")
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

# --- لوحة المدير ---
st.sidebar.divider()
if st.sidebar.button("Admin Panel 👑"):
    st.session_state.show_admin = not st.session_state.show_admin

if st.session_state.get('show_admin'):
    pass_input = st.sidebar.text_input("أدخل كلمة مرور المدير", type="password")
    if pass_input == ADMIN_PASS:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users")
        total_users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM user_files")
        total_files = cur.fetchone()[0]
        cur.close()
        conn.close()
        st.sidebar.success("مرحباً أيها المدير.")
        st.sidebar.info(f"👥 المستخدمون: {total_users}")
        st.sidebar.info(f"📂 الملفات: {total_files}")
    elif pass_input:
        st.sidebar.error("كلمة مرور خاطئة.")

# --- الواجهة الرئيسية ---
st.title(t["title"])
uploaded_file = st.file_uploader(t["upload"], type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        # --- تنظيف البيانات (Data Validation) ---
        df = df.dropna() # حذف الصفوف الفارغة
        df = df.drop_duplicates() # حذف التكرارات
        
        if save_file_to_db(st.session_state.user_email, uploaded_file.name, df):
            st.session_state.df = df
            st.success(f"✅ {uploaded_file.name}")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.df is not None:
    df = st.session_state.df
    st.divider()
    
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()

    if numeric_cols and categorical_cols:
        st.subheader(t["stats"])
        c1, c2, c3 = st.columns(3)
        with c1: st.metric("Total", len(df))
        with c2: st.metric(f"Sum ({numeric_cols[0]})", f"{df[numeric_cols[0]].sum():,.0f}")
        
        best_item = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().idxmax()
        best_value = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().max()
        with c3: st.metric(f"Top ({categorical_cols[0]})", best_item)

        st.divider()
        st.subheader(t["insights"])
        insights = []
        insights.append(f"المنتج الأكثر ربحاً هو '{best_item}' بقيمة إجمالية {best_value:,.0f}. يجب التركيز على توفيره.")
        avg_value = df[numeric_cols[0]].mean()
        insights.append(f"متوسط قيمة العمليات هو {avg_value:,.2f}. إذا كانت التكلفة أعلى من هذا، فأنت تخسر.")
        if len(df) > 10:
            insights.append("حجم البيانات جيد جداً، يمكنك الآن الاعتماد على هذه الأرقام لاتخاذ قراراتك القادمة.")
        else:
            insights.append("حجم البيانات صغير، قد لا تعكس النتائج الواقع بدقة. حاول جمع المزيد من البيانات.")

        for insight in insights:
            st.info(insight)

        st.divider()
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(label=t["export"], data=csv, file_name='report.csv', mime='text/csv')

        st.subheader(t["charts"])
        c1, c2 = st.columns(2)
        with c1: col_x = st.selectbox("Category", categorical_cols)
        with c2: col_y = st.selectbox("Value", numeric_cols)

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

        # --- المحادثة مع البيانات (Chat with Data) ---
        st.divider()
        st.subheader(t["chat"])
        st.write("اسأل عن بياناتك (مثال: ما هو أفضل منتج؟ كم إجمالي المبيعات؟)")
        
        user_question = st.text_input("اكتب سؤالك هنا...")
        
        if user_question:
            if groq_client:
                with st.spinner("الذكاء الاصطناعي يفكر..."):
                    sample_data = df.head(10).to_json(orient='records')
                    prompt = f"""
                    أنت محلل بيانات. لدي بيانات مبيعات (عينة من 10 صفوف):
                    {sample_data}
                    
                    المستخدم يسأل: "{user_question}"
                    
                    أجب على السؤال باللغة العربية بناءً على البيانات. إذا لم تكن الإجابة موجودة، قل ذلك.
                    """
                    try:
                        # جلب الموديلات المتاحة واختيار أول موديل نشط
                        models = groq_client.models.list()
                        available_model = models.data[0].id

                        chat_completion = groq_client.chat.completions.create(
                            messages=[
                                {"role": "system", "content": "أنت محلل بيانات ذكي."},
                                {"role": "user", "content": prompt}
                            ],
                            model=available_model,
                        )
                        st.success(chat_completion.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.warning("يرجى التأكد من إضافة GROQ_API_KEY في إعدادات Streamlit Secrets.")

        with st.expander(t["data"]):
            st.dataframe(df, use_container_width=True)
    else:
        st.warning("⚠️ البيانات غير كافية.")