import polars as pl
import pandas as pd
from prophet import Prophet

class DataEngine:
    def __init__(self, df_polars):
        self.df = df_polars

    def get_basic_stats(self):
        numeric_cols = [c for c in self.df.columns if self.df[c].dtype in [pl.Float64, pl.Int64]]
        if not numeric_cols:
            return {"records": self.df.height, "total": 0}
        total = self.df[numeric_cols[0]].sum()
        return {"records": self.df.height, "total": total}

    def calculate_oee(self):
        df = self.df.to_pandas()
        req = ['Planned_Time_Mins', 'Downtime_Mins', 'Ideal_Cycle_Time_Sec', 'Total_Count', 'Good_Count']
        
        # 1. التحقق من وجود الأعمدة
        if not all(c in df.columns for c in req):
            return None, "Colonnes OEE manquantes"
        
        # 2. التحقق من القيم الفارغة
        if df[req].isnull().any().any():
            return None, "Valeurs manquantes dans les colonnes OEE"

        # 3. التحقق من القيم السالبة
        if (df[req] < 0).any().any():
            return None, "Valeurs négatives détectées"

        # 4. التحقق من أن التوقف لا يتجاوز الوقت المخطط
        if (df['Downtime_Mins'] > df['Planned_Time_Mins']).any():
            return None, "Temps d'arrêt supérieur au temps planifié"

        # 5. التحقق من أن الوقت المخطط ليس صفراً
        if (df['Planned_Time_Mins'] == 0).any():
            return None, "Temps planifié = 0"

        # 6. التحقق من أن القطع السليمة لا تتجاوز الإجمالي
        if (df['Good_Count'] > df['Total_Count']).any():
            return None, "Good_Count > Total_Count"

        try:
            df['Run_Time'] = df['Planned_Time_Mins'] - df['Downtime_Mins']
            df['Availability'] = df['Run_Time'] / df['Planned_Time_Mins']
            
            df['Ideal_Time'] = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']) / 60
            # تجنب القسمة على صفر في Performance
            df['Performance'] = df.apply(lambda row: row['Ideal_Time'] / row['Run_Time'] if row['Run_Time'] > 0 else 0, axis=1)
            
            df['Quality'] = df['Good_Count'] / df['Total_Count']
            df['OEE'] = df['Availability'] * df['Performance'] * df['Quality']
            
            # الحساب الإجمالي (المتوسط الموزون)
            total_planned = df['Planned_Time_Mins'].sum()
            total_run = df['Run_Time'].sum()
            total_ideal = df['Ideal_Time'].sum()
            total_good = df['Good_Count'].sum()
            total_count = df['Total_Count'].sum()
            
            availability = (total_run / total_planned) * 100 if total_planned > 0 else 0
            performance = (total_ideal / total_run) * 100 if total_run > 0 else 0
            quality = (total_good / total_count) * 100 if total_count > 0 else 0
            
            return {
                "availability": availability,
                "performance": performance,
                "quality": quality,
                "oee": (availability * performance * quality) / 10000
            }, None
        except Exception as e:
            return None, str(e)

    def generate_forecast(self, date_col, value_col, periods=3):
        try:
            prophet_df = self.df.to_pandas()[[date_col, value_col]].copy()
            prophet_df.columns = ['ds', 'y']
            prophet_df['ds'] = pd.to_datetime(prophet_df['ds'], errors='coerce')
            prophet_df = prophet_df.dropna(subset=['ds']).groupby('ds').sum().reset_index()
            
            if len(prophet_df) < 2:
                return None, None, "Besoin d'au moins 2 points de données valides."
            
            m = Prophet()
            m.fit(prophet_df)
            future = m.make_future_dataframe(periods=periods, freq='ME')
            forecast = m.predict(future)
            return m, forecast, None
        except Exception as e:
            return None, None, str(e)

    def get_correlation_matrix(self):
        df = self.df.to_pandas()
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) < 2:
            return None
        return numeric_df.corr()
