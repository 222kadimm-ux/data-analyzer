import streamlit as st
import pandas as pd
import plotly.express as px

# 1. إعدادات الصفحة
st.set_page_config(page_title="Pro Data Analyzer", page_icon="💼", layout="wide")

# 2. إدارة الجلسة (لحفظ الملف أثناء التنقل)
if 'df' not in st.session_state:
    st.session_state.df = None
if 'file_name' not in st.session_state:
    st.session_state.file_name = None

# 3. الترجمة
lang = st.sidebar.radio("Language / اللغة", ["العربية", "English"])
t = {
    "العربية": {
        "title": "💼 منصة تحليل البيانات الاحترافية",
        "subtitle": "ارفع ملفك، وقم بتحليله فوراً. (يتم حفظ الملف أثناء جلستك)",
        "upload": "📂 رفع ملف (Excel/CSV)",
        "clear": "🗑️ مسح الملف الحالي",
        "stats": "📊 لوحة القيادة (Dashboard)",
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
        "subtitle": "Upload your file and analyze instantly. (File is saved in your session)",
        "upload": "📂 Upload (Excel/CSV)",
        "clear": "🗑️ Clear Current File",
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

# 4. تصميم CSS احترافي
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 20px; border-radius: 12px; border: 1px solid #3e4257; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stButton>button { width: 100%; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title(t["title"])
st.markdown(f"*{t['subtitle']}*")

# 5. رفع الملف وإدارته
uploaded_file = st.file_uploader(t["upload"], type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        # قراءة الملف وحفظه في الجلسة
        if uploaded_file.name.endswith('.csv'):
            st.session_state.df = pd.read_csv(uploaded_file)
        else:
            st.session_state.df = pd.read_excel(uploaded_file)
        st.session_state.file_name = uploaded_file.name
        st.success(f"✅ {uploaded_file.name} " + ("تم الرفع بنجاح!" if lang == "العربية" else "uploaded successfully!"))
    except Exception as e:
        st.error(f"Error: {e}")

# 6. عرض التحليل إذا كان الملف موجوداً
if st.session_state.df is not None:
    df = st.session_state.df
    
    # زر مسح الملف
    if st.button(t["clear"]):
        st.session_state.df = None
        st.session_state.file_name = None
        st.rerun()

    st.divider()
    
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()

    if numeric_cols and categorical_cols:
        # لوحة القيادة
        st.subheader(t["stats"])
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(t["total_ops"], len(df))
        with col2:
            st.metric(f"{t['total_val']} ({numeric_cols[0]})", f"{df[numeric_cols[0]].sum():,.0f}")
        with col3:
            best = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().idxmax()
            st.metric(f"{t['best_item']} ({categorical_cols[0]})", best)
            
        st.divider()

        # الرسوم البيانية
        st.subheader(t["charts"])
        c1, c2 = st.columns(2)
        
        with c1:
            col_x = st.selectbox(t["col_x"], categorical_cols)
        with c2:
            col_y = st.selectbox(t["col_y"], numeric_cols)

        chart_data = df.groupby(col_x)[col_y].sum().reset_index().sort_values(by=col_y, ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**{t['bar']}**")
            fig_bar = px.bar(chart_data, x=col_x, y=col_y, color=col_y, color_continuous_scale='Teal')
            fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            st.write(f"**{t['pie']}**")
            fig_pie = px.pie(chart_data, names=col_x, values=col_y, hole=0.4)
            fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
            st.plotly_chart(fig_pie, use_container_width=True)

        # البيانات الخام
        with st.expander(t["data"]):
            st.dataframe(df, use_container_width=True)

    else:
        st.warning("⚠️ الملف لا يحتوي على بيانات كافية للتحليل.")
else:
    st.info("💡 " + ("الرجاء رفع ملف للبدء" if lang == "العربية" else "Please upload a file to start"))