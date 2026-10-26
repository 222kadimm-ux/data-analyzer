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
            # التحقق من القيم غير المنطقية
            if (df['Planned_Time_Mins'] <= 0).any():
                return None, "⚠️ الوقت المخطط يجب أن يكون أكبر من صفر."
            if (df['Downtime_Mins'] > df['Planned_Time_Mins']).any():
                return None, "⚠️ وقت التوقف أكبر من الوقت المخطط."
            if (df['Good_Count'] > df['Total_Count']).any():
                return None, "⚠️ عدد القطع السليمة أكبر من إجمالي القطع."
            if (df[req] < 0).any().any():
                return None, "⚠️ البيانات تحتوي على قيم سالبة."
            
            # الحساب من الإجمالي (وليس متوسط النسب)
            total_planned = df['Planned_Time_Mins'].sum()
            total_downtime = df['Downtime_Mins'].sum()
            total_run = total_planned - total_downtime
            
            if total_run <= 0:
                return None, "⚠️ إجمالي وقت التشغيل صفر (توقف كامل)."
            
            availability = (total_run / total_planned) * 100
            
            total_ideal_time = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']).sum() / 60
            performance = (total_ideal_time / total_run) * 100
            
            total_good = df['Good_Count'].sum()
            total_count = df['Total_Count'].sum()
            quality = (total_good / total_count) * 100 if total_count > 0 else 0
            
            oee = (availability * performance * quality) / 10000
            
            if performance < 50:
                warnings.append("⚠️ الأداء منخفض جداً (أقل من 50%). تحقق من الوحدات.")
            if oee > 100:
                warnings.append("⚠️ OEE أكبر من 100% (غير منطقي).")
            
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

    def generate_forecast(self, date_col, value_col, periods=3):
        from prophet import Prophet
        try:
            prophet_df = self.df.to_pandas()[[date_col, value_col]].copy()
            prophet_df.columns = ['ds', 'y']
            prophet_df['ds'] = pd.to_datetime(prophet_df['ds'], errors='coerce')
            prophet_df = prophet_df.dropna(subset=['ds']).groupby('ds').sum().reset_index()
            m = Prophet()
            m.fit(prophet_df)
            future = m.make_future_dataframe(periods=periods, freq='ME')
            forecast = m.predict(future)
            return m, forecast, None
        except Exception as e:
            return None, None, str(e)
