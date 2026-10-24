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
from core_engine import DataEngine
from ai_engine import AIAssistant
from pdf_exporter import PDFExporter

# ... (نفس إعدادات الصفحة والترجمة t) ...

st.set_page_config(page_title="Enterprise Data Analyzer", page_icon="🏭", layout="wide")

# ... (نفس كود الترجمة t هنا) ...

# إنشاء كائنات من الفئات
ai_assistant = AIAssistant()
cookie_manager = stx.CookieManager(key="cookie_manager")

# ... (نفس كود الكوكيز والجلسة) ...

# ==========================================
# الواجهة الرئيسية
# ==========================================
st.title(t["title"])
st.write("Solution professionnelle..." if st.session_state.lang == "FR" else "حل احترافي...")

tab_upload, tab_dashboard, tab_oee, tab_forecast, tab_ai, tab_sql = st.tabs([t["upload_tab"], t["dashboard_tab"], t["oee_tab"], t["forecast_tab"], t["ai_tab"], t["sql_tab"]])

with tab_upload:
    # ... (نفس كود الرفع) ...
    if uploaded_file:
        df = pl.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pl.read_excel(uploaded_file)
        st.session_state.df = df.drop_nulls().unique()
        st.success("✅")

with tab_dashboard:
    if st.session_state.df is not None:
        # استخدام الفئة
        engine = DataEngine(st.session_state.df)
        stats = engine.get_basic_stats()
        c1, c2 = st.columns(2)
        c1.metric("Records", f"{stats['records']:,}")
        c2.metric("Total", f"{stats['total']:,.0f}")

with tab_oee:
    if st.session_state.df is not None:
        engine = DataEngine(st.session_state.df)
        oee_data, error = engine.calculate_oee()
        
        if error:
            st.warning(f"⚠️ {error}")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Disponibilité", f"{oee_data['availability']:.1f}%")
            c2.metric("Performance", f"{oee_data['performance']:.1f}%")
            c3.metric("Qualité", f"{oee_data['quality']:.1f}%")
            c4.metric("OEE", f"{oee_data['oee']:.1f}%")

with tab_forecast:
    if st.session_state.df is not None:
        # ... (نفس كود اختيار التاريخ والقيمة) ...
        if st.button("Générer"):
            engine = DataEngine(st.session_state.df)
            m, forecast, error = engine.generate_forecast(date_col, value_col, periods)
            if error:
                st.error(error)
            else:
                st.pyplot(m.plot(forecast))

with tab_ai:
    if st.session_state.df is not None:
        if st.button(t["report_btn"]):
            with st.spinner("..."):
                # استخدام فئة AI
                report = ai_assistant.generate_report(st.session_state.df, st.session_state.lang)
                st.info(report)
                
                # استخدام فئة PDF
                pdf_file = PDFExporter.generate(report, st.session_state.lang)
                st.download_button(t["download_pdf"], pdf_file, "report.pdf", "application/pdf")

with tab_sql:
    if st.button(t["sql_generate"]):
        generated_sql = ai_assistant.generate_sql(sql_question, sql_table)
        st.code(generated_sql, language="sql")
