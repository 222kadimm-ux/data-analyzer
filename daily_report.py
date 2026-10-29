import pandas as pd
import psycopg2
import resend
from datetime import datetime, timedelta
from settings import DATABASE_URL
from ai_engine import AIAssistant
from pdf_exporter import PDFExporter

# إعدادات البريد
RESEND_API_KEY = "re_xxxxxxxx" # مفتاحك من Resend
resend.api_key = RESEND_API_KEY

def generate_and_send():
    # 1. جلب البيانات من آخر 24 ساعة
    conn = psycopg2.connect(DATABASE_URL)
    query = "SELECT * FROM machine_logs WHERE timestamp > %s"
    df = pd.read_sql(query, conn, params=(datetime.now() - timedelta(days=1),))
    conn.close()
    
    if df.empty:
        print("لا توجد بيانات.")
        return

    # 2. تحليل البيانات بالذكاء الاصطناعي
    ai = AIAssistant(api_key="sk-or-xxxx") # مفتاح OpenRouter
    report_text, success = ai.generate_report(df, "FR")
    
    if not success:
        print("فشل الذكاء الاصطناعي.")
        return

    # 3. تحويل إلى PDF
    pdf_bytes = PDFExporter.generate(report_text, "FR")
    
    # 4. إرسال بالبريد
    resend.Emails.send({
        "from": "reports@yourdomain.com",
        "to": "manager@factory.com",
        "subject": "Rapport Quotidien - Machine 1",
        "html": "<p>Veuillez trouver ci-joint le rapport de la machine.</p>",
        "attachments": [{"filename": "report.pdf", "content": list(pdf_bytes)}]
    })
    print("✅ Email envoyé.")

if __name__ == "__main__":
    generate_and_send()
