import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Analyzer", page_icon="💼", layout="wide")

# 2. إدارة الجلسة (هل المستخدم مسجل دخول أم لا)
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'df' not in st.session_state:
    st.session_state.df = None

# 3. واجهة تسجيل الدخول البسيطة
if not st.session_state.logged_in:
    st.title("🔐 تسجيل الدخول للمنصة")
    st.write("أدخل كلمة المرور للوصول إلى لوحة التحكم.")
    
    password = st.text_input("كلمة المرور", type="password")
    if st.button("تسجيل الدخول"):
        if password == "admin123": # كلمة المرور هي admin123
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("كلمة المرور خاطئة!")
    st.stop() # إيقاف التطبيق هنا حتى يتم تسجيل الدخول

# --- التطبيق يبدأ هنا بعد تسجيل الدخول ---

# الترجمة
lang = st.sidebar.radio("Language / اللغة", ["العربية", "English"])
t = {
    "العربية": {
        "title": "💼 منصة تحليل البيانات الاحترافية",
        "subtitle": "ارفع ملفك، وقم بتحليله فوراً.",
        "upload": "📂 رفع ملف (Excel/CSV)",
        "export": "📥 تحميل التقرير (CSV)",
        "clear": "🗑️ مسح الملف",
        "stats": "📊 لوحة القيادة",
        "total_ops": "إجمالي العمليات",
        "total_val": "إجمالي القيمة",
        "best_item": "أفضل عنصر",
        "charts": "📈 التحليل البياني",
        "col_x": "التصنيف",
        "col_y": "القيمة",
        "bar": "المنتجات الأكثر ربحاً",
        "pie": "توزيع الحصص",
        "data": "📋 البيانات الخام",
        "logout": "🚪 تسجيل الخروج"
    },
    "English": {
        "title": "💼 Pro Data Analytics Platform",
        "subtitle": "Upload your file and analyze instantly.",
        "upload": "📂 Upload (Excel/CSV)",
        "export": "📥 Export Report (CSV)",
        "clear": "🗑️ Clear File",
        "stats": "📊 Dashboard",
        "total_ops": "Total Operations",
        "total_val": "Total Value",
        "best_item": "Top Item",
        "charts": "📈 Charts",
        "col_x": "Category",
        "col_y": "Value",
        "bar": "Most Profitable Items",
        "pie": "Share Distribution",
        "data": "📋 Raw Data",
        "logout": "🚪 Logout"
    }
}[lang]

st.title(t["title"])
st.markdown(f"*{t['subtitle']}*")

# زر تسجيل الخروج
if st.sidebar.button(t["logout"]):
    st.session_state.logged_in = False
    st.rerun()

# رفع الملف
uploaded_file = st.file_uploader(t["upload"], type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.success(f"✅ {uploaded_file.name}")
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.df is not None:
    df = st.session_state.df
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t["clear"]):
            st.session_state.df = None
            st.rerun()
    with col2:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=t["export"],
            data=csv,
            file_name='report.csv',
            mime='text/csv',
        )

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