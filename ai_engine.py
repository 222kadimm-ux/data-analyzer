import streamlit as st
from groq import Groq

try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except:
    client = None

def ask_ai_about_data(user_question, df):
    if not client:
        return "⚠️ مفتاح Groq API غير صالح أو غير موجود."
    
    # بدلاً من إرسال 10 صفوف، نرسل ملخصاً إحصائياً كاملاً
    summary = df.describe(include='all').to_string()
    columns = df.columns.tolist()
    
    prompt = f"""
    أنت محلل بيانات خبير. لديك بيانات بالأعمدة التالية: {columns}
    
    هذا ملخص إحصائي شامل للبيانات:
    {summary}
    
    المستخدم يسأل: "{user_question}"
    
    أجب على السؤال باللغة العربية بناءً على الملخص الإحصائي. كن دقيقاً ومباشراً.
    """
    
    try:
        # استخدام نموذج ثابت وسريع
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "أنت مساعد تحليل بيانات محترف."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}"
