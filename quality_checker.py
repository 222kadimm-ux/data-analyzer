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

        null_counts = self.df.null_count().to_dicts()[0]
        for col, count in null_counts.items():
            if count > 0:
                percentage = (count / self.df.height) * 100
                if percentage > 10:
                    self.issues.append(f"⚠️ العمود '{col}' يحتوي على {percentage:.1f}% قيم فارغة.")
                    self.score -= 10

        numeric_cols = [c for c in self.df.columns if self.df[c].dtype in [pl.Float64, pl.Int64]]
        for col in numeric_cols:
            negatives = self.df.filter(pl.col(col) < 0).height
            if negatives > 0:
                self.issues.append(f"⚠️ العمود '{col}' يحتوي على {negatives} قيماً سالبة.")
                self.score -= 5

        date_cols = [c for c in self.df.columns if 'date' in c.lower() or 'mois' in c.lower()]
        if not date_cols:
            self.issues.append("⚠️ لا يوجد عمود تاريخ. التنبؤ لن يعمل.")
            self.score -= 20

        duplicates = self.df.height - self.df.unique().height
        if duplicates > 0:
            self.issues.append(f"⚠️ يوجد {duplicates} صفوف مكررة.")
            self.score -= 5

        return self.issues, max(0, self.score)

    def get_report(self):
        issues, score = self.run_checks()
        if score >= 90:
            return f"✅ **جودة البيانات ممتازة ({score}/100)**.", issues
        elif score >= 70:
            return f"🟡 **جودة البيانات مقبولة ({score}/100)**.", issues
        else:
            return f"🔴 **جودة البيانات ضعيفة ({score}/100)**.", issues

    # إصلاح: عرض معاينة وإرجاع نسخة جديدة (وليس الحذف التلقائي)
    def get_fix_preview(self):
        df = self.df.clone()
        # حذف التكرارات
        df_unique = df.unique()
        removed = df.height - df_unique.height
        
        # ملء القيم النصية فقط (وليس الرقمية)
        str_cols = [c for c in df_unique.columns if df_unique[c].dtype == pl.Utf8]
        for col in str_cols:
            df_unique = df_unique.with_columns(pl.col(col).fill_null("Inconnu"))
            
        return df_unique, removed
