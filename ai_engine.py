import streamlit as st
import requests
import polars as pl

def ask_ai_about_data(user_question, df_polars):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        return "⚠️ مفتاح API غير موجود."

    # تحويل Polars إلى Pandas مؤقتاً (لإرسال الملخص فقط)
    # نأخذ عينة صغيرة لتوفير الذاكرة إذا كان الملف ضخماً
    if df_polars.height > 10000:
        df_pandas = df_polars.sample(n=10000, seed=42).to_pandas()
    else:
        df_pandas = df_polars.to_pandas()

    try:
        numeric_df = df_pandas.select_dtypes(include=['number'])
        stats = numeric_df.describe().to_string()
        correlations = numeric_df.corr().to_string()
    except:
        stats = "لا توجد أعمدة رقمية كافية."
        correlations = "لا توجد ارتباطات."

    columns = df_polars.columns
    missing = df_pandas.isnull().sum().to_string()
    
    prompt = f"""
    أنت محلل بيانات خبير (Senior Data Analyst). 
    لديك مجموعة بيانات بالأعمدة التالية: {columns}
    
    الإحصائيات الوصفية (Mean, Std, Min, Max):
    {stats}
    
    مصفوفة الارتباطات (Correlations):
    {correlations}
    
    القيم المفقودة:
    {missing}
    
    سؤال المستخدم: "{user_question}"
    
    المطلوب:
    1. أجب على السؤال بدقة بناءً على الأرقام أعلاه.
    2. إذا كان السؤال عاماً، قدم تحليلاً شاملاً.
    3. اكتب الإجابة بلغة عربية احترافية ومنظمة.
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"حدث خطأ: {e}"
