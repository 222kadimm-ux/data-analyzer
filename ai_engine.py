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
            return "⚠️ API Key missing.", False
        
        data = {
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            response = requests.post(self.url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content'], True
        except Exception as e:
            return f"Error: {e}", False

    def generate_report(self, df_polars, lang="FR"):
        # تحويل البيانات إلى Pandas للإحصاء
        df_pandas = df_polars.head(1000).to_pandas()
        columns = df_pandas.columns.tolist()
        stats = df_pandas.describe().to_string()
        sample = df_pandas.head(5).to_string()
        
        lang_name = {"FR": "Français", "AR": "Arabe"}.get(lang, "Français")
        
        # تعديل: نطلب من الذكاء الاصطناعي عدم استخدام الجداول واستخدام النقاط بدلاً منها
        prompt = f"""
        Tu es un analyste de données. 
        Colonnes: {columns}
        Statistiques: {stats}
        Échantillon: {sample}
        
        Donne-moi un rapport complet en {lang_name} avec 3 recommandations.
        
        IMPORTANT: N'utilise PAS de tableaux Markdown. Utilise des listes à puces (bullet points) pour présenter les données.
        """
        return self._call_api(prompt)

    def generate_sql(self, question, table_name):
        # حماية: التحقق من أن الاستعلام آمن
        prompt = f"Génère une requête SQL (SELECT) pour la table `{table_name}`.\nQuestion: {question}\nRéponds uniquement avec le code SQL."
        sql, success = self._call_api(prompt)
        
        if not success:
            return sql, False
        
        # التحقق من أن الاستعلام يبدأ بـ SELECT فقط
        sql_clean = sql.strip().upper()
        if not sql_clean.startswith("SELECT"):
            return "❌ Sécurité: Seules les requêtes SELECT sont autorisées.", False
        if "DROP" in sql_clean or "DELETE" in sql_clean or "UPDATE" in sql_clean or "INSERT" in sql_clean:
            return "❌ Sécurité: Requête interdite.", False
        
        return sql, True
