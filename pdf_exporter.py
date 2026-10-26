from weasyprint import HTML
import html

class PDFExporter:
    @staticmethod
    def generate(report_text, lang="FR"):
        title = "Rapport d'Analyse" if lang == "FR" else "تقرير التحليل"
        direction = "ltr" if lang == "FR" else "rtl"
        
        # التهريب: تحويل أي رموز HTML إلى نصوص آمنة
        safe_report_text = html.escape(report_text).replace('\n', '<br>')
        
        html_content = f"""
        <html dir="{direction}">
        <head><meta charset="utf-8"><style>
            body {{ font-family: Arial; padding: 40px; }}
            h1 {{ color: #4CAF50; text-align: center; }}
            .content {{ line-height: 1.6; }}
        </style></head>
        <body>
            <h1>🏭 {title}</h1>
            <div class="content"><p>{safe_report_text}</p></div>
        </body>
        </html>
        """
        return HTML(string=html_content).write_pdf()
