import streamlit as st
import requests

def ask_ai_about_data(user_question, df):
    # جلب مفتاح OpenRouter من الإعدادات
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        return "⚠️ مفتاح OpenRouter API غير موجود."

    summary = df.describe(include='all').to_string()
    columns = df.columns.tolist()
    
    prompt = f"""
    أنت محلل بيانات خبير. لديك بيانات بالأعمدة التالية: {columns}
    
    هذا ملخص إحصائي شامل للبيانات:
    {summary}
    
    المستخدم يسأل: "{user_question}"
    
    أجب على السؤال باللغة العربية بناءً على الملخص الإحصائي. كن دقيقاً ومباشراً.
    """

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",  # نموذج مجاني
        "messages": [
            {"role": "system", "content": "أنت مساعد تحليل بيانات محترف."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        return f"حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {e}"
