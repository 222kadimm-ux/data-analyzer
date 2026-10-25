import polars as pl
import pandas as pd

class DataQualityChecker:
    def __init__(self, df_polars):
        self.df = df_polars
        self.issues = []
        self.score = 100

    def run_checks(self):
        self.issues = []
        self.score = 100

        # 1. فحص القيم الفارغة
        null_counts = self.df.null_count().to_dicts()[0]
        for col, count in null_counts.items():
            if count > 0:
                percentage = (count / self.df.height) * 100
                if percentage > 10:
                    self.issues.append(f"⚠️ العمود '{col}' يحتوي على {percentage:.1f}% قيم فارغة.")
                    self.score -= 10

        # 2. فحص القيم السالبة في الأعمدة الرقمية
        numeric_cols = [c for c in self.df.columns if self.df[c].dtype in [pl.Float64, pl.Int64]]
        for col in numeric_cols:
            negatives = self.df.filter(pl.col(col) < 0).height
            if negatives > 0:
                self.issues.append(f"⚠️ العمود '{col}' يحتوي على {negatives} قيماً سالبة (غير منطقية).")
                self.score -= 5

        # 3. فحص التواريخ (إذا وجدت)
        date_cols = [c for c in self.df.columns if 'date' in c.lower() or 'mois' in c.lower()]
        if not date_cols:
            self.issues.append("⚠️ لا يوجد عمود تاريخ. التنبؤ بالمستقبل لن يعمل.")
            self.score -= 20

        # 4. فحص التكرارات
        duplicates = self.df.height - self.df.unique().height
        if duplicates > 0:
            self.issues.append(f"⚠️ يوجد {duplicates} صفوف مكررة.")
            self.score -= 5

        return self.issues, max(0, self.score)

    def get_report(self):
        issues, score = self.run_checks()
        if score >= 90:
            return f"✅ **جودة البيانات ممتازة ({score}/100)**. يمكنك التحليل بثقة.", issues
        elif score >= 70:
            return f"🟡 **جودة البيانات مقبولة ({score}/100)**. بعض التحليلات قد تكون غير دقيقة.", issues
        else:
            return f"🔴 **جودة البيانات ضعيفة ({score}/100)**. ننصح بإصلاح الملف قبل التحليل.", issues
