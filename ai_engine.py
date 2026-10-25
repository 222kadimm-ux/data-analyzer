import streamlit as st
import requests

class AIAssistant:
    def __init__(self):
        self.api_key = st.secrets.get("OPENROUTER_API_KEY")
        self.url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _call_api(self, prompt):
        if not self.api_key:
            return "⚠️ API Key missing."
        
        data = {
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {e}"

    def generate_report(self, df_polars, lang="FR"):
        # تحويل البيانات إلى Pandas لأخذ عينة وإحصائيات
        df_pandas = df_polars.head(1000).to_pandas()
        stats = df_pandas.describe().to_string()
        
        # صياغة الطلب (Prompt) لجعل الذكاء الاصطناعي يبدأ بتوصية واحدة
        prompt = f"""
        Tu es un analyste de données senior et un expert en optimisation industrielle.
        Voici les statistiques de production des données fournies:
        {stats}
        
        Ta mission:
        1. Commence par UNE SEULE phrase de recommandation actionnable et directe (ex: "Concentrez-vous immédiatement sur la machine X car elle cause 60% des arrêts").
        2. Rédige ensuite un rapport synthétique (maximum 200 mots) en {'Français' if lang == 'FR' else 'Arabe'}.
        3. Termine par 2 autres recommandations courtes et actionnables.
        
        Sois direct, professionnel et évite les généralités.
        """
        return self._call_api(prompt)

    def generate_sql(self, question, table_name):
        prompt = f"Génère une requête SQL (SELECT) pour la table `{table_name}`.\nQuestion: {question}\nRéponds uniquement avec le code SQL sans markdown."
        return self._call_api(prompt)
