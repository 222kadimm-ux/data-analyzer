import streamlit as st
import requests

def ask_ai_about_data(user_question, df):
    api_key = st.secrets.get("OPENROUTER_API_KEY")
    if not api_key:
        return "⚠️ مفتاح OpenRouter API غير موجود."

    summary = df.describe(include='all').to_string()
    columns = df.columns.tolist()
    
    prompt = f"أنت محلل بيانات. الأعمدة: {columns}. الملخص: {summary}. السؤال: {user_question}. أجب بالعربية."

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": "openrouter/free",
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"حدث خطأ: {e}"
