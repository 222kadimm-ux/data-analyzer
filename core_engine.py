import polars as pl
import pandas as pd
import numpy as np

class DataEngine:
    def __init__(self, df_polars):
        self.df = df_polars

    def get_basic_stats(self):
        numeric_cols = [c for c in self.df.columns if self.df[c].dtype in [pl.Float64, pl.Int64]]
        if not numeric_cols:
            return {"records": self.df.height, "details": []}
        details = []
        for col in numeric_cols:
            details.append({"column": col, "total": self.df[col].sum()})
        return {"records": self.df.height, "details": details}

    def calculate_oee(self):
        df = self.df.to_pandas()
        req = ['Planned_Time_Mins', 'Downtime_Mins', 'Ideal_Cycle_Time_Sec', 'Total_Count', 'Good_Count']
        if not all(c in df.columns for c in req):
            return None, "Colonnes OEE manquantes"
        
        warnings = []
        try:
            # 1. التحقق من القيم غير المنطقية
            if (df['Planned_Time_Mins'] <= 0).any():
                return None, "⚠️ الوقت المخطط يجب أن يكون أكبر من صفر."
            if (df['Downtime_Mins'] > df['Planned_Time_Mins']).any():
                return None, "⚠️ وقت التوقف أكبر من الوقت المخطط."
            if (df['Good_Count'] > df['Total_Count']).any():
                return None, "⚠️ عدد القطع السليمة أكبر من إجمالي القطع."
            if (df[req] < 0).any().any():
                return None, "⚠️ البيانات تحتوي على قيم سالبة."
            
            # 2. معالجة وقت التشغيل الصفري (بدون اختراع أرقام)
            df['Run_Time'] = df['Planned_Time_Mins'] - df['Downtime_Mins']
            
            # إذا كان وقت التشغيل صفراً، الإتاحة = 0 (وليس 1)
            df['Availability'] = np.where(
                df['Run_Time'] == 0, 0, 
                df['Run_Time'] / df['Planned_Time_Mins']
            )
            
            # إذا كان وقت التشغيل صفراً، لا يمكن حساب الأداء (نضعه 0 مع تحذير)
            df['Ideal_Time'] = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']) / 60
            df['Performance'] = np.where(
                df['Run_Time'] == 0, 0,
                df['Ideal_Time'] / df['Run_Time']
            )
            
            if (df['Run_Time'] == 0).any():
                warnings.append("⚠️ بعض الصفوف بها وقت تشغيل صفر (توقف كامل). تم اعتبار الإتاحة والأداء 0 لهذه الصفوف.")

            # 3. الجودة (معالجة إجمالي القطع = 0)
            df['Quality'] = np.where(
                df['Total_Count'] == 0, 0,
                df['Good_Count'] / df['Total_Count']
            )
            
            df['OEE'] = df['Availability'] * df['Performance'] * df['Quality']
            
            # 4. معالجة NaN
            availability = float(np.nan_to_num(df['Availability'].mean() * 100, nan=0.0))
            performance = float(np.nan_to_num(df['Performance'].mean() * 100, nan=0.0))
            quality = float(np.nan_to_num(df['Quality'].mean() * 100, nan=0.0))
            oee = float(np.nan_to_num(df['OEE'].mean() * 100, nan=0.0))
            
            if performance < 50:
                warnings.append("⚠️ الأداء منخفض جداً (أقل من 50%). يرجى التأكد من الوحدات.")
            if oee > 100:
                warnings.append("⚠️ OEE أكبر من 100% (غير منطقي). تحقق من المدخلات.")
            
            result = {
                "availability": availability,
                "performance": performance,
                "quality": quality,
                "oee": oee,
                "warning": " | ".join(warnings) if warnings else None
            }
            return result, None
        except Exception as e:
            return None, str(e)
