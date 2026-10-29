import streamlit as st
import pandas as pd
import polars as pl
import plotly.express as px
import io
import json
import uuid
import datetime
import gspread
import extra_streamlit_components as stx
from google.oauth2.service_account import Credentials
from sqlalchemy import create_engine, text as sql_text
from connectors.sql_database import validate_simple_select
from database import init_db, save_file, get_files, delete_file, get_db_connection, get_file_by_id
from auth import create_user, verify_user, login_user, logout_user
from core_engine import DataEngine
from ai_engine import AIAssistant
from pdf_exporter import PDFExporter
from settings import SENTRY_DSN, DATABASE_URL

# ==========================================
# 1. إعدادات الصفحة والمراقبة
# ==========================================
try:
    import sentry_sdk
except ImportError:
    sentry_sdk = None

st.set_page_config(page_title="Enterprise Data Analyzer", page_icon="🏭", layout="wide")

if sentry_sdk and SENTRY_DSN:
    try:
        sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=1.0, send_default_pii=False)
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
# 2. نظام الترجمة (i18n)
# ==========================================
if 'lang' not in st.session_state:
    st.session_state.lang = "FR"

lang = st.sidebar.selectbox("🌐 Language / Langue", ["FR (Français)", "AR (العربية)"])
st.session_state.lang = "AR" if "AR" in lang else "FR"

t = {
    "FR": {
        "title": "🏭 Enterprise Data Analyzer (OEE & IA)",
        "upload_tab": "1️⃣ Importer Données",
        "dashboard_tab": "2️⃣ Tableau de Bord",
        "oee_tab": "3️⃣ OEE",
        "forecast_tab": "4️⃣ Prévisions",
        "ai_tab": "5️⃣ Assistant IA",
        "sql_tab": "6️⃣ Requête SQL",
        "opcua_tab": "7️⃣ Machines (OPC UA)",
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
        "map_btn": "🔗 Mappage des Colonnes",
        "apply_map": "✅ Appliquer le mappage",
        "map_success": "✅ Mappage réussi ! Allez à l'onglet OEE.",
        "export_data": "📥 Exporter les Données",
        "correlation": "🔗 Matrice de Corrélation",
        "corr_warn": "ℹ️ Besoin de 2 colonnes numériques pour la corrélation.",
        "ai_privacy": "🔒 Confidentialité",
        "ai_toggle": "Autoriser l'IA à analyser les données",
        "ai_disabled": "⚠️ L'IA est désactivée.",
        "access_denied": "❌ Accès refusé à ce fichier.",
        "opcua_download": "📥 Générer le rapport PDF",
        "opcua_ai": "🤖 Analyser avec l'IA",
        "download_pdf_opcua": "📥 Télécharger le PDF"
    },
    "AR": {
        "title": "🏭 محلل بيانات المؤسسات (OEE & AI)",
        "upload_tab": "1️⃣ رفع البيانات",
        "dashboard_tab": "2️⃣ لوحة التحكم",
        "oee_tab": "3️⃣ OEE",
        "forecast_tab": "4️⃣ التنبؤ بالمستقبل",
        "ai_tab": "5️⃣ المساعد الذكي",
        "sql_tab": "6️⃣ اسأل SQL",
        "opcua_tab": "7️⃣ الآلات (OPC UA)",
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
        "map_btn": "🔗 ربط الأعمدة",
        "apply_map": "✅ تطبيق الربط",
        "map_success": "✅ تم الربط بنجاح! اذهب لتبويب OEE.",
        "export_data": "📥 تصدير البيانات",
        "correlation": "🔗 مصفوفة الارتباطات",
        "corr_warn": "ℹ️ تحتاج إلى عمودين رقميين لحساب الارتباط.",
        "ai_privacy": "🔒 الخصوصية",
        "ai_toggle": "السماح للذكاء الاصطناعي بتحليل البيانات",
        "ai_disabled": "⚠️ الذكاء الاصطناعي معطل.",
        "access_denied": "❌ وصول مرفوض لهذا الملف.",
        "opcua_download": "📥 توليد تقرير PDF",
        "opcua_ai": "🤖 تحليل بالذكاء الاصطناعي",
        "download_pdf_opcua": "📥 تحميل تقرير PDF"
    }
}[st.session_state.lang]

# ==========================================
# 3. إدارة الكوكيز
# ==========================================
cookie_manager = stx.CookieManager(key="cookie_manager")

if 'anon_uuid' not in st.session_state:
    saved_uuid = cookie_manager.get(cookie="anon_uuid")
    if saved_uuid:
        st.session_state.anon_uuid = saved_uuid
    else:
        if cookie_manager.get_all() is not None:
            new_uuid = str(uuid.uuid4())
            expiry_date = datetime.datetime.now() + datetime.timedelta(days=365)
            cookie_manager.set("anon_uuid", new_uuid, expires_at=expiry_date)
            st.session_state.anon_uuid = new_uuid
        else:
            st.stop()

current_user = st.session_state.user_email if st.session_state.get('logged_in') else st.session_state.anon_uuid

# ==========================================
# 4. الدوال المساعدة
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
        engine = create_engine(db_url, connect_args={"connect_timeout": 10})
        df_pd = pd.read_sql(f"SELECT * FROM {table_name} LIMIT {limit};", engine)
        return pl.from_pandas(df_pd)
    except Exception as e:
        st.error(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
        return None

def delete_my_account(email):
    conn = cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM user_files WHERE user_email = %s", (email,))
        cur.execute("DELETE FROM users WHERE email = %s", (email,))
        conn.commit()
        return True
    except: return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

# ==========================================
# 5. تهيئة الجلسة
# ==========================================
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = init_db()
if not st.session_state.db_initialized:
    st.sidebar.warning("وضع التشغيل التجريبي: DATABASE_URL غير مضبوط.")

if 'df' not in st.session_state: st.session_state.df = None
if 'raw_df' not in st.session_state: st.session_state.raw_df = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_email' not in st.session_state: st.session_state.user_email = None
if 'last_uploaded_sig' not in st.session_state: st.session_state.last_uploaded_sig = None
if 'ai_report' not in st.session_state: st.session_state.ai_report = None
if 'ai_error' not in st.session_state: st.session_state.ai_error = None
if 'machine_df' not in st.session_state: st.session_state.machine_df = None
if 'opcua_pdf' not in st.session_state: st.session_state.opcua_pdf = None

ai_assistant = AIAssistant()

# ==========================================
# 6. القائمة الجانبية
# ==========================================
st.sidebar.title("Enterprise Data Analyzer")
st.sidebar.info("💾 حفظ دائم مفعّل" if DATABASE_URL else "🧪 وضع تجريبي.")

st.sidebar.divider()
st.sidebar.subheader(t["ai_privacy"])
ai_enabled = st.sidebar.checkbox(t["ai_toggle"], value=True)

if not st.session_state.logged_in and DATABASE_URL:
    with st.sidebar.expander(t["login_portal"]):
        login_email = st.text_input(t["email"], key="l_email")
        login_pass = st.text_input(t["password"], type="password", key="l_pass")
        if st.button("Login / دخول"):
            if verify_user(login_email, login_pass):
                login_user(login_email); st.rerun()
            else: st.error("Error / خطأ")
        
        new_email = st.text_input("Nouveau / جديد", key="n_email")
        new_pass = st.text_input("Mot de passe / كلمة المرور", type="password", key="n_pass")
        if st.button("S'inscrire / إنشاء حساب"):
            if len(new_pass) < 6: st.warning("Short / قصيرة")
            elif create_user(new_email, new_pass): st.success("✅"); st.rerun()
elif not DATABASE_URL:
    st.sidebar.caption("تسجيل الدخول معطّل.")
else:
    st.sidebar.write(f"👤 {st.session_state.user_email}")
    if st.sidebar.button(t["logout"]): logout_user()

st.sidebar.divider()
st.sidebar.subheader(t["saved_work"])
files = get_files(current_user)
if not files: 
    st.sidebar.caption("-")
for f in files:
    col1, col2 = st.sidebar.columns([4, 1])
    if col1.button(f"{f[1]}", key=f"load_{f[0]}"):
        file_data = get_file_by_id(f[0], current_user)
        if file_data:
            data = json.loads(file_data[2]) if isinstance(file_data[2], str) else file_data[2]
            st.session_state.df = pl.from_pandas(pd.DataFrame(data))
            st.session_state.raw_df = st.session_state.df
            st.rerun()
        else:
            st.sidebar.error(t["access_denied"])
    if col2.button("🗑️", key=f"del_{f[0]}"):
        if delete_file(f[0], current_user):
            st.rerun()

# ==========================================
# 7. الواجهة الرئيسية
# ==========================================
st.title(t["title"])
st.write("Solution professionnelle pour l'analyse des données industrielles et commerciales." if st.session_state.lang == "FR" else "حل احترافي لتحليل بيانات المصانع والشركات.")

st.divider()

tab_upload, tab_dashboard, tab_oee, tab_forecast, tab_ai, tab_sql, tab_opcua = st.tabs([t["upload_tab"], t["dashboard_tab"], t["oee_tab"], t["forecast_tab"], t["ai_tab"], t["sql_tab"], t["opcua_tab"]])

with tab_upload:
    option = st.radio("Source de données", ["Fichier / ملف", "Google Sheets", "SQL"])
    
    if "Fichier" in option or "ملف" in option:
        uploaded_file = st.file_uploader(t["file_upload"], type=["xlsx", "csv"])
        
        if uploaded_file:
            if uploaded_file.size > 100 * 1024 * 1024: 
                st.error("🚫 Limite 100MB."); st.stop()
            
            file_signature = f"{uploaded_file.name}_{uploaded_file.size}"
            
            if st.session_state.last_uploaded_sig != file_signature:
                with st.spinner("..."):
                    try:
                        if uploaded_file.name.endswith('.csv'):
                            df = pl.read_csv(uploaded_file, infer_schema_length=10000, ignore_errors=True)
                        else:
                            df = pl.read_excel(uploaded_file)
                        
                        st.session_state.raw_df = df
                        st.session_state.df = df
                        st.session_state.last_uploaded_sig = file_signature
                        save_file(current_user, uploaded_file.name, df.head(5000).to_pandas() if df.height > 5000 else df.to_pandas())
                        st.success(f"✅ Importé avec succès! ({df.height:,})")
                    except Exception as e: 
                        st.error(f"❌ {e}")
            else:
                st.info("ℹ️ الملف مرفوع بالفعل.")

        if st.session_state.raw_df is not None:
            with st.expander(t["map_btn"], expanded=False):
                cols = st.session_state.raw_df.columns
                oee_cols = {
                    "Planned_Time_Mins": "Temps planifié (min)",
                    "Downtime_Mins": "Temps d'arrêt (min)",
                    "Ideal_Cycle_Time_Sec": "Cycle idéal (sec)",
                    "Total_Count": "Production totale",
                    "Good_Count": "Production bonne"
                }
                
                mapping = {}
                col1, col2 = st.columns(2)
                for i, (key, label) in enumerate(oee_cols.items()):
                    with (col1 if i % 2 == 0 else col2):
                        default_idx = 0
                        for j, c in enumerate(cols):
                            if key.lower() in str(c).lower() or label.split()[0].lower() in str(c).lower():
                                default_idx = j + 1
                                break
                        mapping[key] = st.selectbox(f"{label}", options=["-- Ignorer --"] + list(cols), index=default_idx, key=f"map_{key}")
                
                if st.button(t["apply_map"]):
                    if all(v != "-- Ignorer --" for v in mapping.values()):
                        try:
                            rename_dict = {v: k for k, v in mapping.items() if v != "-- Ignorer --"}
                            df_mapped = st.session_state.raw_df.rename(rename_dict)
                            st.session_state.df = df_mapped
                            save_file(current_user, f"Mapped_{uploaded_file.name}", df_mapped.head(5000).to_pandas())
                            st.success(t["map_success"])
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ {e}")
                    else:
                        st.warning("⚠️ Veuillez sélectionner une colonne pour chaque champ.")

    elif "Google" in option:
        st.info("💡 **Pour les entreprises:** Partagez votre Google Sheet avec cet email (Viewer): `sheets-bot@data-analyzer-512419.iam.gserviceaccount.com`")
        gs_url = st.text_input("URL Google Sheets:")
        if st.button("Import / سحب"):
            if gs_url:
                df = load_from_gsheets(gs_url)
                if df is not None: 
                    st.session_state.df = df
                    st.session_state.raw_df = df
                    save_file(current_user, "Google_Sheets", df.head(5000).to_pandas())
                    st.success("✅")
                else: st.error("❌")

    elif "SQL" in option:
        st.info("💡 Contactez votre service IT pour obtenir l'URL de votre base de données." if st.session_state.lang == "FR" else "💡 اتصل بقسم تقنية المعلومات للحصول على رابط قاعدة البيانات.")
        db_url = st.text_input("URL (postgresql://...)", type="password")
        table_name = st.text_input("Table:")
        if st.button("Import / سحب"):
            if db_url and table_name:
                df = load_from_sql(db_url, table_name)
                if df is not None: 
                    st.session_state.df = df
                    st.session_state.raw_df = df
                    save_file(current_user, "SQL_Data", df.to_pandas())
                    st.success("✅")
                else: st.error("❌")

with tab_dashboard:
    if st.session_state.df is None: 
        st.info(t["no_data"])
    else:
        engine = DataEngine(st.session_state.df)
        stats = engine.get_basic_stats()
        
        c1, c2 = st.columns(2)
        c1.metric("Records / سجلات", f"{stats['records']:,}")
        c2.metric("Total", f"{stats['total']:,.0f}")

        st.divider()
        st.subheader(t["correlation"])
        corr_matrix = engine.get_correlation_matrix()
        if corr_matrix is not None:
            fig = px.imshow(corr_matrix, text_auto=True, aspect="auto", color_continuous_scale='RdBu')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(t["corr_warn"])

        st.divider()
        st.subheader(t["export_data"])
        df_export = st.session_state.df.to_pandas()
        c1, c2 = st.columns(2)
        c1.download_button("Télécharger CSV", df_export.to_csv(index=False).encode('utf-8-sig'), "data.csv", "text/csv")
        
        excel_buffer = io.BytesIO()
        df_export_excel = df_export.copy()
        for col in df_export_excel.select_dtypes(include=['datetimetz']).columns:
            df_export_excel[col] = df_export_excel[col].dt.tz_localize(None)
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_export_excel.to_excel(writer, index=False)
        c2.download_button("Télécharger Excel", excel_buffer.getvalue(), "data.xlsx")

with tab_oee:
    if st.session_state.df is None: st.info(t["no_data"])
    else:
        engine = DataEngine(st.session_state.df)
        oee_data, error = engine.calculate_oee()
        if error:
            st.warning(f"⚠️ {error}")
            st.info("💡 **Suggestion:** Vos données ne contiennent pas les colonnes OEE." if st.session_state.lang == "FR" else "💡 **اقتراح:** بياناتك لا تحتوي على أعمدة OEE.")
            
            df = st.session_state.df.to_pandas()
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                st.write("**Colonnes numériques disponibles:**" if st.session_state.lang == "FR" else "**الأعمدة الرقمية المتاحة:**")
                for col in numeric_cols:
                    st.write(f"- {col} (Moyenne / المتوسط: {df[col].mean():.2f}, Max: {df[col].max():.2f})")
                
                st.write("**Analyse alternative suggérée:**" if st.session_state.lang == "FR" else "**تحليل بديل مقترح:**")
                st.bar_chart(df[numeric_cols[0]].head(20))
            else:
                st.error("❌ Aucune colonne numérique trouvée." if st.session_state.lang == "FR" else "❌ لا توجد أعمدة رقمية.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Disponibilité / الإتاحة", f"{oee_data['availability']:.1f}%")
            c2.metric("Performance / الأداء", f"{oee_data['performance']:.1f}%")
            c3.metric("Qualité / الجودة", f"{oee_data['quality']:.1f}%")
            c4.metric("OEE", f"{oee_data['oee']:.1f}%")

with tab_forecast:
    if st.session_state.df is None: st.info(t["no_data"])
    else:
        df = st.session_state.df.to_pandas()
        date_cols = [c for c in df.columns if 'date' in c.lower() or 'mois' in c.lower()]
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        if not date_cols or not numeric_cols:
            st.warning("⚠️ Besoin d'une colonne Date et numérique." if st.session_state.lang == "FR" else "⚠️ تحتاج إلى عمود للتاريخ وعمود رقمي.")
        else:
            col1, col2 = st.columns(2)
            date_col = col1.selectbox("Colonne Date:", date_cols)
            value_col = col2.selectbox("Colonne Valeur:", numeric_cols)
            periods = st.slider("Périodes futures:", 1, 12, 3)
            
            if st.button("Générer les prévisions"):
                with st.spinner("..."):
                    engine = DataEngine(st.session_state.df)
                    m, forecast, error = engine.generate_forecast(date_col, value_col, periods)
                    if error: st.error(f"❌ {error}")
                    else:
                        st.success("✅")
                        st.pyplot(m.plot(forecast))

with tab_ai:
    if st.session_state.df is None: 
        st.info(t["no_data"])
    elif not ai_enabled:
        st.warning(t["ai_disabled"])
    else:
        if st.button(t["report_btn"]):
            with st.spinner("..."):
                report, success = ai_assistant.generate_report(st.session_state.df, st.session_state.lang)
                if success:
                    st.session_state.ai_report = report
                    st.session_state.ai_error = None
                else:
                    st.session_state.ai_error = report
                    st.session_state.ai_report = None
        
        if st.session_state.ai_report:
            st.info(st.session_state.ai_report)
            pdf_file = PDFExporter.generate(st.session_state.ai_report, st.session_state.lang)
            st.download_button(t["download_pdf"], pdf_file, "report.pdf", "application/pdf")
        
        if st.session_state.ai_error:
            st.error(st.session_state.ai_error)
        
        question = st.text_input("Question / سؤال:")
        if st.button("Envoyer / إرسال"):
            if question: 
                answer, success = ai_assistant._call_api(question)
                if success: st.success(answer)
                else: st.error(answer)

with tab_sql:
    sql_db_url = st.text_input(t["sql_url"], type="password", key="sql_db")
    sql_table = st.text_input(t["sql_table"], key="sql_table")
    sql_question = st.text_input(t["sql_question"], key="sql_q")

    if st.button(t["sql_generate"]):
        if sql_db_url and sql_table and sql_question:
            with st.spinner("..."):
                generated_sql, success = ai_assistant.generate_sql(sql_question, sql_table)
                if success:
                    st.code(generated_sql, language="sql")
                    db_engine = None
                    try:
                        checked_sql = validate_simple_select(generated_sql, sql_table.strip())
                        db_engine = create_engine(sql_db_url, pool_pre_ping=True, pool_recycle=300)
                        with db_engine.connect() as connection:
                            result = connection.execute(sql_text(checked_sql))
                            result_df = pd.DataFrame(result.fetchall(), columns=result.keys())
                        st.success(f"✅ ({len(result_df)} lignes)")
                        st.dataframe(result_df, use_container_width=True)
                    except Exception as exc:
                        st.error(f"❌ Requête non exécutée : {exc}")
                    finally:
                        if db_engine is not None:
                            db_engine.dispose()
                else:
                    st.error(generated_sql)
        else:
            st.warning("Fill all fields / املأ الحقول")

with tab_opcua:
    st.subheader("🔌 Connexion aux Machines (OPC UA)")
    st.info("💡 Lance une lecture continue de 10 secondes sur le serveur OPC UA, puis affiche les valeurs collectées.")

    opc_url = st.text_input("URL du serveur OPC UA:", value="opc.tcp://opcuademo.sterfive.com:26543", key="opc_url")
    opc_node = st.text_input("Node ID:", value="ns=0;i=2258", key="opc_node")

    if st.button("🔗 Se connecter et lire pendant 10 secondes", key="opc_read_stream"):
        if opc_url and opc_node:
            with st.spinner("Connexion et lecture en cours..."):
                try:
                    from connectors.opcua_connector import OPCUAConnector
                    connector = OPCUAConnector(opc_url, opc_node)
                    data = connector.start_streaming(duration_sec=10, interval_sec=1)
                    if data:
                        machine_df = pd.DataFrame(data)
                        machine_df["timestamp"] = pd.to_datetime(machine_df["timestamp"], unit="s", errors="coerce")
                        st.session_state.machine_df = machine_df
                        st.success(f"✅ {len(machine_df)} valeurs collectées.")
                        st.metric("Dernière valeur lue", str(machine_df["value"].iloc[-1]))
                        machine_df["value_numeric"] = pd.to_numeric(machine_df["value"], errors="coerce")
                        chart_df = machine_df.dropna(subset=["timestamp", "value_numeric"])
                        if not chart_df.empty:
                            st.line_chart(chart_df.set_index("timestamp")["value_numeric"])
                        st.dataframe(machine_df, use_container_width=True)
                    else:
                        st.warning("Aucune valeur n'a été reçue du serveur OPC UA.")
                except Exception as exc:
                    st.error(f"❌ Erreur OPC UA : {exc}")
        else:
            st.warning("⚠️ Veuillez entrer l'URL et le Node ID.")

    # --- الأزرار تظهر خارج زر الاتصال ---
    if st.session_state.machine_df is not None:
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(t["opcua_download"], key="btn_gen_pdf"):
                report_text = f"Rapport OPC UA\n\nServeur: {opc_url}\nNode: {opc_node}\n\nValeurs lues:\n{st.session_state.machine_df.to_string()}"
                pdf_file = PDFExporter.generate(report_text, st.session_state.lang)
                st.session_state.opcua_pdf = pdf_file
            
            if st.session_state.opcua_pdf:
                st.download_button(
                    label="📥 Télécharger le PDF",
                    data=st.session_state.opcua_pdf,
                    file_name="rapport_opcua.pdf",
                    mime="application/pdf",
                    key="btn_dl_pdf"
                )
        
        with col2:
            if st.button(t["opcua_ai"], key="btn_ai_analyze"):
                with st.spinner("L'IA analyse..."):
                    machine_pl = pl.from_pandas(st.session_state.machine_df)
                    report, success = ai_assistant.generate_report(machine_pl, st.session_state.lang)
                    if success:
                        st.info(report)
                    else:
                        st.error(report)
