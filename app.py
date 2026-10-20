import streamlit as st
import pandas as pd

# 1. إعدادات الصفحة الاحترافية
st.set_page_config(page_title="محلل البيانات الذكي", page_icon="📊", layout="wide")

# 2. تصميم مخصص (CSS) لإعطاء طابع المنصات العالمية
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3e4257; }
    .stDataFrame { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 المنصة الذكية لتحليل البيانات")
st.markdown("*ارفع ملف الإكسيل وسأقوم بتحليله واستخراج أهم النتائج لك فوراً.*")

# 3. رفع الملف
uploaded_file = st.file_uploader("📂 اختر ملف الإكسيل (Excel) أو (CSV)", type=["xlsx", "csv"])

if uploaded_file is not None:
    # قراءة البيانات
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success("✅ تم رفع الملف بنجاح! جاري التحليل...")
        st.divider()

        # 4. الإحصائيات الذكية (KPIs)
        st.subheader("📈 النتائج الأولية")
        
        # محاولة اكتشاف الأعمدة تلقائياً
        numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()

        if numeric_cols and categorical_cols:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="إجمالي العمليات", value=len(df))
            
            with col2:
                total_sum = df[numeric_cols[0]].sum()
                st.metric(label=f"إجمالي {numeric_cols[0]}", value=f"{total_sum:,.0f}")
            
            with col3:
                best_item = df.groupby(categorical_cols[0])[numeric_cols[0]].sum().idxmax()
                st.metric(label=f"أفضل {categorical_cols[0]}", value=best_item)
            
            st.divider()

            # 5. الرسوم البيانية
            st.subheader("📊 تحليل المنتجات")
            
            # اختيار الأعمدة
            col_x = st.selectbox("اختر عمود التصنيف (مثلاً: اسم المنتج)", categorical_cols)
            col_y = st.selectbox("اختر عمود القيمة (مثلاً: المبلغ)", numeric_cols)

            # تجميع البيانات
            chart_data = df.groupby(col_x)[col_y].sum().reset_index().sort_values(by=col_y, ascending=False)

            # عرض رسمين بيانيين (أعمدة ودائري)
            c1, c2 = st.columns(2)
            with c1:
                st.write("**توزيع المبيعات (أعمدة)**")
                st.bar_chart(chart_data.set_index(col_x)[col_y])
            with c2:
                st.write("**النسبة المئوية (دائري)**")
                # سنستخدم دالة altair المدمجة في streamlit
                st.write("") # مسافة
                st.write(chart_data)

            # 6. الجدول الكامل
            st.subheader("📋 عرض البيانات الكاملة")
            st.dataframe(df, use_container_width=True)

        else:
            st.warning("⚠️ الملف لا يحتوي على أعمدة رقمية ونصية كافية للتحليل.")
            
    except Exception as e:
        st.error(f"❌ حدث خطأ أثناء قراءة الملف: {e}")
else:
    st.info("💡 يرجى رفع ملف إكسيل للبدء. (تأكد أن الملف يحتوي على أعمدة مثل 'المنتج' و 'المبلغ').")