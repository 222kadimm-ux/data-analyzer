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
            # إضافة timeout=30 لمنع التجمد
            response = requests.post(self.url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.exceptions.Timeout:
            return "⚠️ انتهت مهلة الاتصال بالذكاء الاصطناعي. يرجى المحاولة مرة أخرى."
        except Exception as e:
            return f"Error: {e}"

    def generate_report(self, df_polars, lang="FR"):
        df_pandas = df_polars.head(1000).to_pandas()
        stats = df_pandas.describe().to_string()
        prompt = f"""
        Tu es un analyste de données senior et un expert en optimisation industrielle.
        Voici les statistiques de production des données fournies:
        {stats}
        
        Ta mission:
        1. Commence par UNE SEULE phrase de recommandation actionnable et directe.
        2. Rédige ensuite un rapport synthétique (maximum 200 mots) en {'Français' if lang == 'FR' else 'Arabe'}.
        3. Termine par 2 autres recommandations courtes et actionnables.
        """
        return self._call_api(prompt)

    def generate_sql(self, question, table_name):
        prompt = f"Génère une requête SQL (SELECT) pour la table `{table_name}`.\nQuestion: {question}\nRéponds uniquement avec le code SQL sans markdown."
        return self._call_api(prompt)
