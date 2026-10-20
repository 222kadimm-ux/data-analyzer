import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. إعدادات الصفحة
st.set_page_config(page_title="Data Analyzer", page_icon="📊", layout="wide")

# 2. نظام الترجمة (عربي / إنجليزي)
lang = st.sidebar.radio("Language / اللغة", ["العربية", "English"])

translations = {
    "العربية": {
        "title": "📊 المنصة الذكية لتحليل البيانات",
        "subtitle": "ارفع ملف الإكسيل وسأقوم بتحليله واستخراج أهم النتائج لك فوراً.",
        "upload": "📂 اختر ملف الإكسيل (Excel) أو (CSV)",
        "success": "✅ تم رفع الملف بنجاح!",
        "stats": "📈 النتائج الأولية",
        "total_ops": "إجمالي العمليات",
        "total_val": "إجمالي القيمة",
        "best_item": "أفضل عنصر",
        "charts": "📊 تحليل البيانات",
        "col_x": "اختر عمود التصنيف (مثلاً: المنتج)",
        "col_y": "اختر عمود القيمة (مثلاً: المبلغ)",
        "bar_chart": "توزيع القيم",
        "pie_chart": "النسبة المئوية",
        "table": "📋 عرض البيانات الكاملة",
        "warning": "⚠️ يرجى رفع ملف يحتوي على أعمدة رقمية ونصية.",
        "info": "💡 يرجى رفع ملف إكسيل للبدء."
    },
    "English": {
        "title": "📊 Smart Data Analysis Platform",
        "subtitle": "Upload your Excel file and I will analyze it to extract key insights instantly.",
        "upload": "📂 Upload Excel (XLSX) or (CSV) file",
        "success": "✅ File uploaded successfully!",
        "stats": "📈 Initial Insights",
        "total_ops": "Total Operations",
        "total_val": "Total Value",
        "best_item": "Top Item",
        "charts": "📊 Data Analysis",
        "col_x": "Select Categorical Column (e.g., Product)",
        "col_y": "Select Numeric Column (e.g., Amount)",
        "bar_chart": "Value Distribution",
        "pie_chart": "Percentage Breakdown",
        "table": "📋 Full Data View",
        "warning": "⚠️ File must contain numeric and categorical columns.",
        "info": "💡 Please upload an Excel file to start."
    }
}

t = translations[lang]

# 3. تصميم مخصص
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4257; }
    </style>
""", unsafe_allow_html=True)

st.title(t["title"])
st.markdown(f"*{t['subtitle']}*")

# 4. رفع الملف
uploaded_file = st.file_uploader(t["upload"], type=["xlsx", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(t["success"])
        st.divider()

        # 5. الإحصائيات
        st.subheader(t["stats"])
        
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()

        if numeric_cols and categorical_cols:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label=t["total_ops"], value=len(df))
            
            with col2:
                total_sum = df[numeric_cols[0]].sum()
                st.metric(label=f"{t['total_val']} ({numeric_cols[0]})", value=f"{total_sum:,.0f}")
            
            with col3:
                best_item = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().idxmax()
                st.metric(label=f"{t['best_item']} ({categorical_cols[0]})", value=best_item)
            
            st.divider()

            # 6. الرسوم البيانية
            st.subheader(t["charts"])
            
            col_x = st.selectbox(t["col_x"], categorical_cols)
            col_y = st.selectbox(t["col_y"], numeric_cols)

            chart_data = df.groupby(col_x)[col_y].sum().reset_index().sort_values(by=col_y, ascending=False)

            c1, c2 = st.columns(2)
            
            with c1:
                st.write(f"**{t['bar_chart']}**")
                fig_bar = px.bar(chart_data, x=col_x, y=col_y, color=col_y, color_continuous_scale='Blues')
                fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                st.plotly_chart(fig_bar, use_container_width=True)

            with c2:
                st.write(f"**{t['pie_chart']}**")
                fig_pie = px.pie(chart_data, names=col_x, values=col_y, hole=0.4)
                fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                st.plotly_chart(fig_pie, use_container_width=True)

            # 7. الجدول
            st.subheader(t["table"])
            st.dataframe(df, use_container_width=True)

        else:
            st.warning(t["warning"])
            
    except Exception as e:
        st.error(f"❌ Error: {e}")
else:
    st.info(t["info"])