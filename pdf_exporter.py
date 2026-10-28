from weasyprint import HTML, CSS
import markdown
import datetime

class PDFExporter:
    @staticmethod
    def generate(report_text, lang="FR"):
        # 1. إصلاح Markdown (تحويل الرموز إلى HTML)
        html_body = markdown.markdown(report_text, extensions=['tables', 'fenced_code'])
        
        title = "Rapport d'Analyse" if lang == "FR" else "تقرير التحليل"
        direction = "ltr" if lang == "FR" else "rtl"
        
        # 2. تجهيز HTML مع تنسيق CSS وخط يدعم العربية
        html_content = f"""
        <html dir="{direction}">
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ 
                    font-family: 'DejaVu Sans', 'Arial', sans-serif; 
                    font-size: 12pt; 
                    line-height: 1.6; 
                    color: #333;
                }}
                h1 {{ color: #4CAF50; text-align: center; }}
                h2 {{ color: #2E7D32; border-bottom: 1px solid #ccc; padding-bottom: 5px; }}
                h3 {{ color: #388E3C; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: {direction}; }}
                th {{ background-color: #f2f2f2; }}
                .footer {{ text-align: center; font-size: 10pt; color: #888; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <h1>🏭 {title}</h1>
            <div class="content">
                {html_body}
            </div>
            <div class="footer">
                Généré par Enterprise Data Analyzer | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
            </div>
        </body>
        </html>
        """
        
        # 3. توليد PDF
        return HTML(string=html_content).write_pdf()
