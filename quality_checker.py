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

        # 2. فحص القيم السالبة
        numeric_cols = [c for c in self.df.columns if self.df[c].dtype in [pl.Float64, pl.Int64]]
        for col in numeric_cols:
            negatives = self.df.filter(pl.col(col) < 0).height
            if negatives > 0:
                self.issues.append(f"⚠️ العمود '{col}' يحتوي على {negatives} قيماً سالبة.")
                self.score -= 5

        # 3. فحص التواريخ
        date_cols = [c for c in self.df.columns if 'date' in c.lower() or 'mois' in c.lower()]
        if not date_cols:
            self.issues.append("⚠️ لا يوجد عمود تاريخ. التنبؤ لن يعمل.")
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
            return f"✅ **جودة البيانات ممتازة ({score}/100)**.", issues
        elif score >= 70:
            return f"🟡 **جودة البيانات مقبولة ({score}/100)**.", issues
        else:
            return f"🔴 **جودة البيانات ضعيفة ({score}/100)**.", issues

    # دالة الإصلاح التلقائي
    def auto_fix(self):
        df = self.df.clone()
        
        # 1. حذف التكرارات
        df = df.unique()
        
        # 2. ملء القيم الفارغة (فقط للأعمدة غير الحرجة)
        critical_cols = ['Planned_Time_Mins', 'Downtime_Mins', 'Total_Count', 'Good_Count']
        
        numeric_cols = [c for c in df.columns if df[c].dtype in [pl.Float64, pl.Int64]]
        for col in numeric_cols:
            if col not in critical_cols:
                mean_val = df[col].mean()
                if mean_val is not None:
                    df = df.with_columns(pl.col(col).fill_null(mean_val))
        
        # 3. ملء القيم النصية الفارغة
        str_cols = [c for c in df.columns if df[c].dtype == pl.Utf8]
        for col in str_cols:
            df = df.with_columns(pl.col(col).fill_null("Inconnu"))
            
        return df
