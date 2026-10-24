from weasyprint import HTML

class PDFExporter:
    @staticmethod
    def generate(report_text, lang="FR"):
        title = "Rapport d'Analyse" if lang == "FR" else "تقرير التحليل"
        direction = "ltr" if lang == "FR" else "rtl"
        
        html_content = f"""
        <html dir="{direction}">
        <head><meta charset="utf-8"><style>
            body {{ font-family: Arial; padding: 40px; }}
            h1 {{ color: #4CAF50; text-align: center; }}
            .content {{ line-height: 1.6; }}
        </style></head>
        <body>
            <h1>🏭 {title}</h1>
            <div class="content"><p>{report_text.replace('\n', '<br>')}</p></div>
        </body>
        </html>
        """
        return HTML(string=html_content).write_pdf()
