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
from core_engine import DataEngine, fetch_shopify_data
from ai_engine import AIAssistant
from pdf_exporter import PDFExporter
from quality_checker import DataQualityChecker

# ==========================================
# 1. إعدادات الصفحة
# ==========================================
st.set_page_config(page_title="Enterprise Data Analyzer", page_icon="🏭", layout="wide")

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
# 2. نظام الترجمة (i18n) - إضافة الإنجليزية
# ==========================================
if 'lang' not in st.session_state:
    st.session_state.lang = "FR"

lang = st.sidebar.selectbox("🌐 Language / Langue / اللغة", ["FR (Français)", "AR (العربية)", "EN (English)"])
if "AR" in lang: st.session_state.lang = "AR"
elif "EN" in lang: st.session_state.lang = "EN"
else: st.session_state.lang = "FR"

t = {
    "FR": {
        "title": "🏭 Enterprise Data Analyzer (OEE & IA)",
        "upload_tab": "1️⃣ Importer Données",
        "dashboard_tab": "2️⃣ Tableau de Bord",
        "oee_tab": "3️⃣ OEE",
        "forecast_tab": "4️⃣ Prévisions",
        "ai_tab": "5️⃣ Assistant IA",
        "sql_tab": "6️⃣ Requête SQL",
        "file_upload": "Choisir un fichier Excel ou CSV",
        "no_data": "⚠️ Veuillez importer des données d'abord.",
        "saved_work": "🗂️ Vos fichiers précédents",
        "login_portal": "🔒 Portail Employés (Optionnel)",
        "logout": "Déconnexion",
        "email": "Email",
        "password": "Mot de passe",
        "sql_url": "1. URL de la base de données (postgresql://...)",
        "sql_table": "2. Nom de la table:",
        "sql_question": "3. Votre question:",
        "sql_generate": "Générer et exécuter",
        "report_btn": "📝 Générer un rapport automatique",
        "download_pdf": "📥 Télécharger le rapport en PDF",
    },
    "AR": {
        "title": "🏭 محلل بيانات المؤسسات (OEE & AI)",
        "upload_tab": "1️⃣ رفع البيانات",
        "dashboard_tab": "2️⃣ لوحة التحكم",
        "oee_tab": "3️⃣ OEE",
        "forecast_tab": "4️⃣ التنبؤ بالمستقبل",
        "ai_tab": "5️⃣ المساعد الذكي",
        "sql_tab": "6️⃣ اسأل SQL",
        "file_upload": "اختر ملف Excel أو CSV",
        "no_data": "⚠️ يرجى رفع البيانات أولاً.",
        "saved_work": "🗂️ ملفاتك السابقة",
        "login_portal": "🔒 بوابة الموظفين (اختياري)",
        "logout": "تسجيل الخروج",
        "email": "البريد الإلكتروني",
        "password": "كلمة المرور",
        "sql_url": "1. رابط قاعدة البيانات (postgresql://...)",
        "sql_table": "2. اسم الجدول:",
        "sql_question": "3. سؤالك:",
        "sql_generate": "توليد وتنفيذ الاستعلام",
        "report_btn": "📝 تقرير تلقائي",
        "download_pdf": "📥 تحميل التقرير كـ PDF",
    },
    "EN": {
        "title": "🏭 Enterprise Data Analyzer (OEE & AI)",
        "upload_tab": "1️⃣ Import Data",
        "dashboard_tab": "2️⃣ Dashboard",
        "oee_tab": "3️⃣ OEE",
        "forecast_tab": "4️⃣ Forecast",
        "ai_tab": "5️⃣ AI Assistant",
        "sql_tab": "6️⃣ SQL Query",
        "file_upload": "Choose an Excel or CSV file",
        "no_data": "⚠️ Please import data first.",
        "saved_work": "🗂️ Your previous files",
        "login_portal": "🔒 Employee Portal (Optional)",
        "logout": "Logout",
        "email": "Email",
        "password": "Password",
        "sql_url": "1. Database URL (postgresql://...)",
        "sql_table": "2. Table name:",
        "sql_question": "3. Your question:",
        "sql_generate": "Generate & Execute",
        "report_btn": "📝 Generate Auto Report",
        "download_pdf": "📥 Download Report as PDF",
    }
}[st.session_state.lang]

# ==========================================
# 3. إدارة الكوكيز والدوال المساعدة
# ==========================================
cookie_manager = stx.CookieManager(key="cookie_manager")

if 'anon_uuid' not in st.session_state:
    saved_uuid = cookie_manager.get(cookie="anon_uuid")
    if saved_uuid:
        st.session_state.anon_uuid = saved_uuid
    else:
        new_uuid = str(uuid.uuid4())
        cookie_manager.set("anon_uuid", new_uuid)
        st.session_state.anon_uuid = new_uuid

current_user = st.session_state.user_email if st.session_state.get('logged_in') else st.session_state.anon_uuid

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

ai_assistant = AIAssistant()

# ==========================================
# 5. القائمة الجانبية
# ==========================================
st.sidebar.title("Enterprise Data Analyzer")
st.sidebar.info("💾 Sauvegarde automatique activée / الحفظ التلقائي مفعل" if st.session_state.lang == "FR" else ("💾 Auto-Save Enabled" if st.session_state.lang == "EN" else "💾 الحفظ التلقائي مفعل"))

if not st.session_state.logged_in:
    with st.sidebar.expander(t["login_portal"]):
        login_email = st.text_input(t["email"], key="l_email")
        login_pass = st.text_input(t["password"], type="password", key="l_pass")
        if st.button("Login / دخول / Login"):
            if verify_user(login_email, login_pass):
                login_user(login_email); st.rerun()
            else: st.error("Error / خطأ")
        
        new_email = st.text_input("New Email / بريد جديد / Nouvel Email", key="n_email")
        new_pass = st.text_input("New Password / كلمة مرور جديدة", type="password", key="n_pass")
        if st.button("Register / إنشاء حساب / S'inscrire"):
            if len(new_pass) < 6: st.warning("Short / قصيرة")
            elif create_user(new_email, new_pass): st.success("✅"); st.rerun()
else:
    st.sidebar.write(f"👤 {st.session_state.user_email}")
    if st.sidebar.button(t["logout"]): logout_user()

st.sidebar.divider()
st.sidebar.subheader(t["saved_work"])
files = get_files(current_user)
if not files: st.sidebar.caption("-")
for f in files:
    col1, col2 = st.sidebar.columns([4, 1])
    if col1.button(f"{f[1]}", key=f"load_{f[0]}"):
        data = json.loads(f[2]) if isinstance(f[2], str) else f[2]
        st.session_state.df = pl.from_pandas(pd.DataFrame(data)); st.rerun()
    if col2.button("🗑️", key=f"del_{f[0]}"):
        delete_file(f[0], current_user); st.rerun()

# ==========================================
# 6. الواجهة الرئيسية
# ==========================================
st.title(t["title"])
st.write("Solution professionnelle..." if st.session_state.lang == "FR" else ("Professional solution for industrial data analysis." if st.session_state.lang == "EN" else "حل احترافي لتحليل بيانات المصانع والشركات."))

st.divider()

tab_upload, tab_dashboard, tab_oee, tab_forecast, tab_ai, tab_sql = st.tabs([t["upload_tab"], t["dashboard_tab"], t["oee_tab"], t["forecast_tab"], t["ai_tab"], t["sql_tab"]])

with tab_upload:
    option = st.radio("Source de données / مصدر البيانات / Data Source", ["Fichier / ملف / File", "Google Sheets", "SQL", "Shopify"])
    
    if "Fichier" in option or "ملف" in option or "File" in option:
        uploaded_file = st.file_uploader(t["file_upload"], type=["xlsx", "csv"])
        if uploaded_file:
            if uploaded_file.size > 100 * 1024 * 1024: st.error("🚫 Limite 100MB."); st.stop()
            with st.spinner("..."):
                try:
                    df = pl.read_csv(uploaded_file, infer_schema_length=10000, ignore_errors=True) if uploaded_file.name.endswith('.csv') else pl.read_excel(uploaded_file)
                    df = df.drop_nulls().unique()
                    st.session_state.df = df
                    save_file(current_user, uploaded_file.name, df.head(5000).to_pandas() if df.height > 5000 else df.to_pandas())
                    st.success(f"✅ Importé avec succès! ({df.height:,})")
                    
                    checker = DataQualityChecker(df)
                    report_msg, issues = checker.get_report()
                    if issues:
                        st.warning(report_msg)
                        with st.expander("🔍 Voir les problèmes / عرض المشاكل / View Issues"):
                            for issue in issues: st.write(issue)
                    else: st.success(report_msg)
                except Exception as e: st.error(f"❌ {e}")

    elif "Google" in option:
        st.info("💡 **Pour les entreprises:** Partagez votre Google Sheet avec cet email (Viewer): `sheets-bot@data-analyzer-512419.iam.gserviceaccount.com`")
        gs_url = st.text_input("URL Google Sheets:")
        if st.button("Import / سحب"):
            if gs_url:
                df = load_from_gsheets(gs_url)
                if df is not None: 
                    st.session_state.df = df
                    save_file(current_user, "Google_Sheets", df.head(5000).to_pandas())
                    st.success("✅")
                else: st.error("❌")

    elif "SQL" in option:
        st.info("💡 Contactez votre service IT..." if st.session_state.lang != "AR" else "💡 اتصل بقسم تقنية المعلومات...")
        db_url = st.text_input("URL (postgresql://...)", type="password")
        table_name = st.text_input("Table:")
        if st.button("Import / سحب"):
            if db_url and table_name:
                df = load_from_sql(db_url, table_name)
                if df is not None: 
                    st.session_state.df = df
                    save_file(current_user, "SQL_Data", df.to_pandas())
                    st.success("✅")
                else: st.error("❌")

    elif "Shopify" in option:
        st.info("💡 Connectez votre boutique Shopify / اربط متجرك / Connect your store")
        shop_url = st.text_input("Shop URL (e.g., my-store.myshopify.com):")
        api_key = st.text_input("API Key:", type="password")
        password = st.text_input("API Password:", type="password")
        if st.button("Fetch Shopify Data / جلب البيانات"):
            if shop_url and api_key and password:
                with st.spinner("..."):
                    df = fetch_shopify_data(shop_url, api_key, password)
                    if df is not None:
                        st.session_state.df = df
                        save_file(current_user, "Shopify_Data", df.to_pandas())
                        st.success("✅ Shopify Data Imported!")
                    else: st.error("❌ Failed to connect to Shopify. Check your credentials.")

with tab_dashboard:
    if st.session_state.df is None: st.info(t["no_data"])
    else:
        engine = DataEngine(st.session_state.df)
        stats = engine.get_basic_stats()
        c1, c2 = st.columns(2)
        c1.metric("Records / سجلات", f"{stats['records']:,}")
        c2.metric("Total", f"{stats['total']:,.0f}")

with tab_oee:
    if st.session_state.df is None: st.info(t["no_data"])
    else:
        engine = DataEngine(st.session_state.df)
        oee_data, error = engine.calculate_oee()
        if error:
            st.warning(f"⚠️ {error}")
            st.info("💡 **Suggestion:** Vos données ne contiennent pas les colonnes OEE. Voulez-vous analyser une autre métrique ?" if st.session_state.lang == "FR" else ("💡 **Suggestion:** Your data doesn't contain OEE columns. Analyze another metric?" if st.session_state.lang == "EN" else "💡 **اقتراح:** بياناتك لا تحتوي على أعمدة OEE. هل تريد تحليل مقياس آخر؟"))
            
            df = st.session_state.df.to_pandas()
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                st.write("**Colonnes numériques disponibles:**" if st.session_state.lang == "FR" else ("**Available numeric columns:**" if st.session_state.lang == "EN" else "**الأعمدة الرقمية المتاحة:**"))
                for col in numeric_cols:
                    st.write(f"- {col} (Moyenne / المتوسط: {df[col].mean():.2f}, Max: {df[col].max():.2f})")
                
                st.write("**Analyse alternative suggérée:**" if st.session_state.lang == "FR" else ("**Suggested alternative analysis:**" if st.session_state.lang == "EN" else "**تحليل بديل مقترح:**"))
                st.bar_chart(df[numeric_cols[0]].head(20))
            else:
                st.error("❌ Aucune colonne numérique trouvée." if st.session_state.lang == "FR" else ("❌ No numeric columns found." if st.session_state.lang == "EN" else "❌ لا توجد أعمدة رقمية."))
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Disponibilité / الإتاحة / Availability", f"{oee_data['availability']:.1f}%")
            c2.metric("Performance / الأداء / Performance", f"{oee_data['performance']:.1f}%")
            c3.metric("Qualité / الجودة / Quality", f"{oee_data['quality']:.1f}%")
            c4.metric("OEE", f"{oee_data['oee']:.1f}%")

with tab_forecast:
    if st.session_state.df is None: st.info(t["no_data"])
    else:
        df = st.session_state.df.to_pandas()
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'mois' in c.lower()]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not date_cols or not numeric_cols:
            st.warning("⚠️ Besoin d'une colonne Date et numérique." if st.session_state.lang == "FR" else ("⚠️ Need a Date and numeric column." if st.session_state.lang == "EN" else "⚠️ تحتاج إلى عمود للتاريخ وعمود رقمي."))
        else:
            col1, col2 = st.columns(2)
            date_col = col1.selectbox("Colonne Date:", date_cols)
            value_col = col2.selectbox("Colonne Valeur:", numeric_cols)
            periods = st.slider("Périodes futures:", 1, 12, 3)
            
            if st.button("Générer les prévisions / توليد التنبؤ / Generate Forecast"):
                with st.spinner("..."):
                    engine = DataEngine(st.session_state.df)
                    m, forecast, error = engine.generate_forecast(date_col, value_col, periods)
                    if error: st.error(f"❌ {error}")
                    else:
                        st.success("✅")
                        st.pyplot(m.plot(forecast))

with tab_ai:
    if st.session_state.df is None: st.info(t["no_data"])
    else:
        if st.button(t["report_btn"]):
            with st.spinner("..."):
                report = ai_assistant.generate_report(st.session_state.df, st.session_state.lang)
                st.info(report)
                
                pdf_file = PDFExporter.generate(report, st.session_state.lang)
                st.download_button(t["download_pdf"], pdf_file, "report.pdf", "application/pdf")
        
        question = st.text_input("Question / سؤال / Question:")
        if st.button("Envoyer / إرسال / Send"):
            if question: st.success(ai_assistant._call_api(question))

with tab_sql:
    sql_db_url = st.text_input(t["sql_url"], type="password", key="sql_db")
    sql_table = st.text_input(t["sql_table"], key="sql_table")
    sql_question = st.text_input(t["sql_question"], key="sql_q")
    
    if st.button(t["sql_generate"]):
        if sql_db_url and sql_table and sql_question:
            with st.spinner("..."):
                generated_sql = ai_assistant.generate_sql(sql_question, sql_table)
                st.code(generated_sql, language="sql")
                try:
                    engine = create_engine(sql_db_url)
                    result_df = pd.read_sql(generated_sql, engine)
                    st.success(f"✅ ({len(result_df)})")
                    st.dataframe(result_df)
                except Exception as e:
                    st.error(f"❌ {e}")
        else:
            st.warning("Fill all fields / املأ الحقول")
