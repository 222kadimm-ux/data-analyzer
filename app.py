import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
import bcrypt
import json
import io
import random
import string
import requests
from groq import Groq
import extra_streamlit_components as stx

# --- إعدادات قاعدة البيانات ---
DB_URL = "postgresql://neondb_owner:npg_qVub1K6DCvcz@ep-purple-mud-b5sns22j-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

st.set_page_config(page_title="Pro Data Analyzer", page_icon="💼", layout="wide")

# --- إعدادات الذكاء الاصطناعي والبريد ---
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    groq_client = None

try:
    EMAILJS_SERVICE_ID = st.secrets["EMAILJS_SERVICE_ID"]
    EMAILJS_TEMPLATE_ID = st.secrets["EMAILJS_TEMPLATE_ID"]
    EMAILJS_PUBLIC_KEY = st.secrets["EMAILJS_PUBLIC_KEY"]
    email_service_active = True
except Exception:
    email_service_active = False

# --- إدارة الكوكيز ---
cookie_manager = stx.CookieManager(key="cookie_manager")

# --- دوال قاعدة البيانات ---
def get_db_connection():
    return psycopg2.connect(DB_URL)

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6)) # رمز من 6 أحرف

def send_email_js(to_email, token, is_reset=False):
    if not email_service_active:
        return False
    try:
        url = "https://api.emailjs.com/api/v1.0/email/send"
        
        # إذا كان للاستعادة، نرسل كلمة "Reset" في الموضوع (يمكنك تعديل القالب لاحقاً)
        subject = "استعادة كلمة المرور" if is_reset else "رمز التحقق"
        
        payload = {
            "service_id": EMAILJS_SERVICE_ID,
            "template_id": EMAILJS_TEMPLATE_ID,
            "user_id": EMAILJS_PUBLIC_KEY,
            "template_params": {
                "to_email": to_email,
                "token": token,
                "subject": subject
            }
        }
        response = requests.post(url, json=payload)
        print("EMAILJS RESPONSE:", response.text) # لمراقبة الأخطاء في Terminal
        return response.status_code == 200
    except Exception as e:
        return False

def create_user(email, password, security_answer):
    conn = get_db_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    token = generate_token()
    try:
        cur.execute("INSERT INTO users (email, password_hash, security_answer, verify_token) VALUES (%s, %s, %s, %s)", (email, hashed, security_answer, token))
        conn.commit()
        
        email_sent = send_email_js(email, token, is_reset=False)
        if email_sent:
            st.success("✅ تم إنشاء الحساب! يرجى التحقق من بريدك الإلكتروني لتفعيل الحساب.")
        else:
            st.warning("⚠️ تم إنشاء الحساب، لكن تعذر إرسال البريد. تواصل مع الدعم.")
            cur.execute("UPDATE users SET email_verified = TRUE WHERE email = %s", (email,))
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
    cur.execute("SELECT password_hash, email_verified FROM users WHERE email = %s", (email,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        if not result[1]:
            return "unverified"
        if bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
            return True
    return False

def verify_token(token):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET email_verified = TRUE, verify_token = NULL WHERE verify_token = %s RETURNING email", (token,))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return result is not None

def request_password_reset(email):
    conn = get_db_connection()
    cur = conn.cursor()
    token = generate_token()
    cur.execute("UPDATE users SET reset_token = %s WHERE email = %s RETURNING email", (token, email))
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    if result:
        email_sent = send_email_js(email, token, is_reset=True)
        return email_sent
    return False

def reset_password(email, token, new_password):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT reset_token FROM users WHERE email = %s", (email,))
    result = cur.fetchone()
    
    if result and result[0] == token:
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cur.execute("UPDATE users SET password_hash = %s, reset_token = NULL WHERE email = %s", (hashed, email))
        conn.commit()
        cur.close()
        conn.close()
        return True
    cur.close()
    conn.close()
    return False

def save_file_to_db(email, filename, df):
    conn = get_db_connection()
    cur = conn.cursor()
    json_data = df.to_json(orient='records')
    try:
        cur.execute("INSERT INTO user_files (user_email, file_name, file_data) VALUES (%s, %s, %s)", (email, filename, json_data))
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
    except Exception:
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
if 'show_privacy' not in st.session_state:
    st.session_state.show_privacy = False
if 'show_verify' not in st.session_state:
    st.session_state.show_verify = False
if 'show_reset_request' not in st.session_state:
    st.session_state.show_reset_request = False
if 'show_reset_confirm' not in st.session_state:
    st.session_state.show_reset_confirm = False

# --- التحقق من رابط التفعيل ---
query_params = st.query_params
if "verify" in query_params:
    token = query_params["verify"]
    if verify_token(token):
        st.success("✅ تم تفعيل حسابك بنجاح! يمكنك الآن تسجيل الدخول.")
    else:
        st.error("❌ رابط التفعيل غير صالح أو مستخدم مسبقاً.")
    st.stop()

# --- استرجاع الجلسة ---
if not st.session_state.logged_in:
    saved_session = cookie_manager.get(cookie="app_session")
    if saved_session:
        try:
            session_data = json.loads(saved_session)
            st.session_state.logged_in = True
            st.session_state.user_email = session_data["email"]
            st.rerun()
        except:
            pass

# --- شاشة تسجيل الدخول ---
if not st.session_state.logged_in:
    st.title("🔐 مرحباً بك في منصة تحليل البيانات")
    
    # 1. شاشة طلب استعادة كلمة المرور
    if st.session_state.show_reset_request:
        st.subheader("🔑 استعادة كلمة المرور")
        st.write("أدخل بريدك الإلكتروني وسنرسل لك رمزاً.")
        reset_email = st.text_input("البريد الإلكتروني")
        if st.button("إرسال الرمز"):
            if request_password_reset(reset_email):
                st.success("✅ تم إرسال الرمز إلى بريدك الإلكتروني.")
                st.session_state.show_reset_request = False
                st.session_state.show_reset_confirm = True
                st.session_state.reset_email_temp = reset_email # لحفظ البريد مؤقتاً
                st.rerun()
            else:
                st.error("❌ البريد الإلكتروني غير مسجل أو تعذر الإرسال.")
        if st.button("العودة"):
            st.session_state.show_reset_request = False
            st.rerun()

    # 2. شاشة إدخال الرمز وكلمة المرور الجديدة
    elif st.session_state.show_reset_confirm:
        st.subheader("🔑 تغيير كلمة المرور")
        st.write(f"تم إرسال الرمز إلى: {st.session_state.get('reset_email_temp', '')}")
        token_input = st.text_input("رمز الاستعادة")
        new_pass = st.text_input("كلمة المرور الجديدة", type="password")
        if st.button("تغيير كلمة المرور"):
            if reset_password(st.session_state.get('reset_email_temp'), token_input, new_pass):
                st.success("✅ تم تغيير كلمة المرور بنجاح! يمكنك تسجيل الدخول.")
                st.session_state.show_reset_confirm = False
                st.rerun()
            else:
                st.error("❌ الرمز غير صحيح.")
        if st.button("العودة"):
            st.session_state.show_reset_confirm = False
            st.rerun()

    elif st.session_state.show_privacy:
        st.subheader("📜 سياسة الخصوصية وشروط الاستخدام")
        st.write("""
        **سياسة الخصوصية:**
        نحن نحترم خصوصيتك. جميع البيانات التي ترفعها يتم تشفيرها وتخزينها في قاعدة بيانات آمنة. لا نشارك بياناتك مع أي طرف ثالث. يمكنك حذف بياناتك في أي وقت من خلال لوحة التحكم.
        
        **شروط الاستخدام:**
        هذا التطبيق مخصص لتحليل البيانات. يمنع استخدامه لأي أغراض غير قانونية. نحن غير مسؤولين عن أي قرارات تتخذها بناءً على تحليلات المنصة.
        """)
        if st.button("العودة"):
            st.session_state.show_privacy = False
            st.rerun()

    elif st.session_state.show_verify:
        st.subheader("📧 تفعيل الحساب")
        st.write("أدخل الرمز الذي أرسلناه إلى بريدك الإلكتروني:")
        token_input = st.text_input("رمز التحقق")
        if st.button("تفعيل"):
            if verify_token(token_input):
                st.success("✅ تم التفعيل! يمكنك الآن تسجيل الدخول.")
                st.session_state.show_verify = False
                st.rerun()
            else:
                st.error("رمز غير صحيح.")
        if st.button("العودة"):
            st.session_state.show_verify = False
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["تسجيل الدخول", "إنشاء حساب جديد"])
        with tab1:
            login_email = st.text_input("البريد الإلكتروني", key="login_email")
            login_pass = st.text_input("كلمة المرور", type="password", key="login_pass")
            remember_me = st.checkbox("تذكرني (حفظ الجلسة)")
            
            if st.button("دخول", type="primary"):
                status = verify_user(login_email, login_pass)
                if status is True:
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_email
                    if remember_me:
                        session_data = json.dumps({"email": login_email})
                        cookie_manager.set("app_session", session_data)
                    st.rerun()
                elif status == "unverified":
                    st.error("⚠️ يرجى تفعيل بريدك الإلكتروني أولاً.")
                    st.session_state.show_verify = True
                    st.rerun()
                else:
                    st.error("البريد الإلكتروني أو كلمة المرور غير صحيحة.")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("نسيت كلمة المرور؟"):
                    st.session_state.show_reset_request = True
                    st.rerun()
            with col2:
                if st.button("سياسة الخصوصية"):
                    st.session_state.show_privacy = True
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
                    st.session_state.show_verify = True
                    st.rerun()
                else:
                    st.error("هذا البريد الإلكتروني مسجل مسبقاً.")
    st.stop()

# --- التطبيق بعد تسجيل الدخول (بقية الكود كما هو) ---
st.sidebar.write(f"👤 {st.session_state.user_email}")
lang = st.sidebar.radio("Language / اللغة", ["العربية", "English"])
t = {
    "العربية": {
        "title": "💼 منصة تحليل البيانات الاحترافية",
        "upload": "📂 رفع ملف جديد (Excel/CSV)",
        "history": "🗂️ ملفاتي السابقة",
        "export": "📥 تحميل التقرير (CSV)",
        "export_excel": "📥 تحميل التقرير (Excel)",
        "clear": "🗑️ مسح الشاشة",
        "stats": "📊 لوحة القيادة",
        "charts": "📈 التحليل البياني",
        "data": "📋 البيانات الخام",
        "insights": "🧠 التحليل الذكي",
        "demo": "📊 عرض بيانات تجريبية",
        "chat": "💬 المحادثة مع البيانات (AI)",
        "gdpr": "📤 تصدير بياناتي (GDPR)",
        "search": "🔍 البحث والتصفية"
    },
    "English": {
        "title": "💼 Pro Data Analytics Platform",
        "upload": "📂 Upload New File (Excel/CSV)",
        "history": "🗂️ My Previous Files",
        "export": "📥 Export Report (CSV)",
        "export_excel": "📥 Export Report (Excel)",
        "clear": "🗑️ Clear Screen",
        "stats": "📊 Dashboard",
        "charts": "📈 Charts",
        "data": "📋 Raw Data",
        "insights": "🧠 Smart Insights",
        "demo": "📊 Show Demo Data",
        "chat": "💬 Chat with Data (AI)",
        "gdpr": "📤 Export My Data (GDPR)",
        "search": "🔍 Search & Filter"
    }
}[lang]

if st.sidebar.button(t["demo"]):
    demo_data = {
        'Product': ['Shirt', 'Pants', 'Shoes', 'Jacket', 'Shirt', 'Shoes'],
        'Amount': [1500, 2500, 4000, 6000, 1500, 4000],
        'Month': ['Jan', 'Jan', 'Feb', 'Feb', 'Mar', 'Mar']
    }
    st.session_state.df = pd.DataFrame(demo_data)
    st.rerun()

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

if st.sidebar.button(t["gdpr"]):
    all_data = {"files": [{"name": f[1], "data": f[2]} for f in user_files]}
    st.sidebar.download_button(
        label="تحميل البيانات",
        data=json.dumps(all_data, ensure_ascii=False, indent=4),
        file_name=f"my_data_{st.session_state.user_email}.json",
        mime="application/json"
    )

if st.sidebar.button(t["clear"]):
    st.session_state.df = None
    st.rerun()
if st.sidebar.button("تسجيل الخروج"):
    cookie_manager.delete("app_session")
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.df = None
    st.rerun()

st.title(t["title"])
uploaded_file = st.file_uploader(t["upload"], type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        df = df.dropna()
        df = df.drop_duplicates()
        
        if save_file_to_db(st.session_state.user_email, uploaded_file.name, df):
            st.session_state.df = df
            st.success(f"✅ {uploaded_file.name}")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.df is not None:
    df = st.session_state.df
    st.divider()
    
    st.subheader(t["search"])
    search_query = st.text_input("ابحث عن منتج أو قيمة معينة (اتركه فارغاً لعرض الكل):")
    if search_query:
        mask = df.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        df = df[mask]
        if df.empty:
            st.warning("⚠️ لا توجد نتائج مطابقة لبحثك.")
            st.stop()
        else:
            st.success(f"تم العثور على {len(df)} نتيجة.")
            
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
        insights = [
            f"المنتج الأكثر ربحاً هو '{best_item}' بقيمة إجمالية {best_value:,.0f}. يجب التركيز على توفيره.",
            f"متوسط قيمة العمليات هو {df[numeric_cols[0]].mean():,.2f}. إذا كانت التكلفة أعلى من هذا، فأنت تخسر."
        ]
        if len(df) > 10:
            insights.append("حجم البيانات جيد جداً، يمكنك الآن الاعتماد على هذه الأرقام لاتخاذ قراراتك القادمة.")
        else:
            insights.append("حجم البيانات صغير، قد لا تعكس النتائج الواقع بدقة. حاول جمع المزيد من البيانات.")
        for insight in insights:
            st.info(insight)

        st.divider()
        col_csv, col_excel = st.columns(2)
        with col_csv:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(label=t["export"], data=csv, file_name='report.csv', mime='text/csv')
        with col_excel:
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
            excel_data = excel_buffer.getvalue()
            st.download_button(label=t["export_excel"], data=excel_data, file_name='report.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

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

        st.divider()
        st.subheader(t["chat"])
        user_question = st.text_input("اكتب سؤالك هنا...")
        if user_question:
            if groq_client:
                with st.spinner("الذكاء الاصطناعي يفكر..."):
                    sample_data = df.head(10).to_json(orient='records')
                    prompt = f"أنت محلل بيانات. لدي بيانات مبيعات (عينة من 10 صفوف):\n{sample_data}\n\nالمستخدم يسأل: \"{user_question}\"\n\nأجب على السؤال باللغة العربية بناءً على البيانات. إذا لم تكن الإجابة موجودة، قل ذلك."
                    try:
                        models = groq_client.models.list()
                        available_model = models.data[0].id
                        chat_completion = groq_client.chat.completions.create(
                            messages=[{"role": "system", "content": "أنت محلل بيانات ذكي."}, {"role": "user", "content": prompt}],
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