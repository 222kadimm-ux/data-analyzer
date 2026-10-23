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

# تهيئة Sentry
try:
    sentry_sdk.init(dsn=st.secrets.get("SENTRY_DSN", ""), traces_sample_rate=1.0)
except Exception:
    pass

# تصميم مريح للعين (Dark Mode)
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
# 2. تهيئة الجلسة وقاعدة البيانات
# ==========================================
if 'db_initialized' not in st.session_state:
    init_db()
    st.session_state.db_initialized = True

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'df' not in st.session_state: st.session_state.df = None
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
# 3. شاشة تسجيل الدخول
# ==========================================
if not st.session_state.logged_in:
    st.title("🔐 مرحباً بك في منصة تحليل البيانات")
    
    if st.session_state.show_privacy:
        st.subheader("📜 سياسة الخصوصية")
        st.write("نحن نحترم خصوصيتك. يتم تشفير كلمات المرور. لا نشارك بياناتك مع أي طرف ثالث. يمكنك حذف حسابك في أي وقت.")
        if st.button("العودة"):
            st.session_state.show_privacy = False
            st.rerun()
    else:
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
            
            if st.button("دخول"):
                if verify_user(login_email, login_pass):
                    st.session_state.login_attempts = 0
                    login_user(login_email)
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.session_state.last_attempt_time = time.time()
                    st.error(f"بيانات خاطئة. المحاولة {st.session_state.login_attempts}/5")
            
            if st.button("سياسة الخصوصية"):
                st.session_state.show_privacy = True
                st.rerun()
                    
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
# 4. القائمة الجانبية
# ==========================================
st.sidebar.write(f"👤 {st.session_state.user_email}")

if st.session_state.user_role == "admin":
    st.sidebar.page_link("pages/1_Admin_Panel.py", label="👑 لوحة المدير", icon="👑")

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
        except Exception as e:
            st.sidebar.error(f"خطأ: {e}")
    if col2.button("🗑️", key=f"del_{f[0]}"):
        delete_file(f[0], st.session_state.user_email)
        st.rerun()

st.sidebar.divider()
with st.sidebar.expander("⚙️ إدارة الحساب"):
    st.write("سيتم حذف جميع بياناتك وملفاتك نهائياً.")
    if st.button("🗑️ حذف حسابي"):
        if delete_my_account(st.session_state.user_email):
            st.success("تم حذف الحساب بنجاح.")
            logout_user()
        else:
            st.error("حدث خطأ أثناء الحذف.")

if st.sidebar.button("تسجيل الخروج"):
    logout_user()

# ==========================================
# 5. الواجهة الرئيسية
# ==========================================
st.title("💼 محلل البيانات الاحترافي (AI Data Analyst)")
st.write("قم برفع ملفك للحصول على تحليل إحصائي متقدم وتقارير ذكية.")

tab_upload, tab_dashboard, tab_ai = st.tabs(["1️⃣ رفع البيانات", "2️⃣ لوحة التحكم الإحصائية", "3️⃣ المساعد الذكي (AI)"])

with tab_upload:
    st.subheader("📂 ارفع ملفك هنا")
    uploaded_file = st.file_uploader("اختر ملف Excel أو CSV", type=["xlsx", "csv"])
    
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
                    st.success(f"✅ تم رفع {uploaded_file.name} بنجاح! اذهب للتبويب الثاني.")
            except Exception as e:
                st.error(f"خطأ في قراءة الملف: {e}")

with tab_dashboard:
    if st.session_state.df is None:
        st.info("⚠️ لا توجد بيانات. يرجى رفع ملف أولاً من التبويب الأول.")
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
        else:
            st.warning("البيانات لا تحتوي على أعمدة رقمية ونصية كافية.")

with tab_ai:
    if st.session_state.df is None:
        st.info("⚠️ لا توجد بيانات. يرجى رفع ملف أولاً من التبويب الأول.")
    else:
        st.subheader("💬 المساعد الذكي (AI Analyst)")
        st.write("اطلب تقريراً كاملاً أو اسأل عن بياناتك.")
        
        if st.button("📝 توليد تقرير تحليلي تلقائي"):
            with st.spinner("الذكاء الاصطناعي يحلل البيانات ويكتب التقرير..."):
                report = ask_ai_about_data("أعطني تقريراً تحليلياً شاملاً عن هذه البيانات، واذكر أهم 3 توصيات.", st.session_state.df)
                st.info(report)
        
        st.divider()
        
        question = st.text_input("اسأل سؤالاً محدداً (مثلاً: ما هو المنتج الأكثر ربحية؟):")
        if st.button("إرسال السؤال"):
            if question:
                with st.spinner("جاري التحليل..."):
                    answer = ask_ai_about_data(question, st.session_state.df)
                    st.success(answer)
            else:
                st.warning("اكتب سؤالك أولاً.")
