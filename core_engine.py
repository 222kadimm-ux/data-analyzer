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
        if not all(c in df.columns for c in req):
            return None, "Colonnes OEE manquantes"
        
        try:
            df['Run_Time'] = df['Planned_Time_Mins'] - df['Downtime_Mins']
            df['Availability'] = df['Run_Time'] / df['Planned_Time_Mins']
            df['Ideal_Time'] = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']) / 60
            df['Performance'] = df['Ideal_Time'] / df['Run_Time']
            df['Quality'] = df['Good_Count'] / df['Total_Count']
            df['OEE'] = df['Availability'] * df['Performance'] * df['Quality']
            
            return {
                "availability": df['Availability'].mean() * 100,
                "performance": df['Performance'].mean() * 100,
                "quality": df['Quality'].mean() * 100,
                "oee": df['OEE'].mean() * 100
            }, None
        except Exception as e:
            return None, str(e)

    def generate_forecast(self, date_col, value_col, periods=3):
        try:
            prophet_df = self.df.to_pandas()[[date_col, value_col]].copy()
            prophet_df.columns = ['ds', 'y']
            prophet_df['ds'] = pd.to_datetime(prophet_df['ds'], errors='coerce')
            prophet_df = prophet_df.dropna(subset=['ds']).groupby('ds').sum().reset_index()
            
            # تحسين F5: اكتشاف التردد تلقائياً (يومي، أسبوعي، شهري)
            if len(prophet_df) > 1:
                diff = (prophet_df['ds'].iloc[1] - prophet_df['ds'].iloc[0]).days
                if diff <= 1: freq = 'D'
                elif diff <= 7: freq = 'W'
                else: freq = 'ME'
            else:
                freq = 'ME'
            
            m = Prophet()
            m.fit(prophet_df)
            future = m.make_future_dataframe(periods=periods, freq=freq)
            forecast = m.predict(future)
            return m, forecast, None
        except Exception as e:
            return None, None, str(e)

    def get_correlation_matrix(self):
        # إضافة F4: مصفوفة الارتباطات
        df = self.df.to_pandas()
        numeric_df = df.select_dtypes(include=['number'])
        if len(numeric_df.columns) < 2:
            return None
        return numeric_df.corr()
