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

        # 2. فحص القيم السالبة (فقط في أعمدة الإنتاج، وليس المبيعات)
        production_cols = ['Planned_Time_Mins', 'Downtime_Mins', 'Total_Count', 'Good_Count']
        for col in production_cols:
            if col in self.df.columns:
                negatives = self.df.filter(pl.col(col) < 0).height
                if negatives > 0:
                    self.issues.append(f"⚠️ العمود '{col}' يحتوي على {negatives} قيماً سالبة.")
                    self.score -= 5

        # 3. فحص التواريخ (تحذير فقط للتنبؤ)
        date_cols = [c for c in self.df.columns if 'date' in c.lower() or 'mois' in c.lower()]
        if not date_cols:
            self.issues.append("ℹ️ لا يوجد عمود تاريخ. التنبؤ الزمني لن يعمل (لكن التحليل يعمل).")
            self.score -= 5 # خصم أقل

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

    def get_fix_preview(self):
        """إرجاع معاينة الإصلاح (دون تغيير الأصل)"""
        df = self.df.clone()
        changes = []
        
        # حذف التكرارات
        df_unique = df.unique()
        removed = df.height - df_unique.height
        if removed > 0:
            changes.append(f"حذف {removed} صفوف مكررة.")
        
        # ملء القيم النصية فقط
        str_cols = [c for c in df_unique.columns if df_unique[c].dtype == pl.Utf8]
        for col in str_cols:
            null_count = df_unique.filter(pl.col(col).is_null()).height
            if null_count > 0:
                df_unique = df_unique.with_columns(pl.col(col).fill_null("Inconnu"))
                changes.append(f"ملء {null_count} قيم فارغة في '{col}'.")
            
        return df_unique, changes
