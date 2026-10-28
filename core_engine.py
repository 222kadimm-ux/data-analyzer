import polars as pl
import pandas as pd
import numpy as np

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
        """Calculate OEE after validating all inputs and edge cases.

        OEE = availability × performance × quality. Values are returned as
        percentages for the three components and a percentage for overall OEE.
        """
        df = self.df.to_pandas().copy()
        req = ['Planned_Time_Mins', 'Downtime_Mins', 'Ideal_Cycle_Time_Sec', 'Total_Count', 'Good_Count']
        missing = [c for c in req if c not in df.columns]
        if missing:
            return None, f"Colonnes OEE manquantes: {', '.join(missing)}"
        try:
            df[req] = df[req].apply(pd.to_numeric, errors='raise')
        except (TypeError, ValueError):
            return None, "Les colonnes OEE doivent contenir uniquement des nombres."

        values = df[req].to_numpy(dtype=float)
        if not (values == values).all() or not np.isfinite(values).all():
            return None, "Valeurs manquantes ou non finies dans les colonnes OEE."
        if (df[req] < 0).any().any():
            return None, "Valeurs négatives détectées."
        if (df['Ideal_Cycle_Time_Sec'] <= 0).any():
            return None, "Ideal_Cycle_Time_Sec doit être strictement positif."
        if (df['Planned_Time_Mins'] <= 0).any():
            return None, "Planned_Time_Mins doit être strictement positif."
        if (df['Downtime_Mins'] > df['Planned_Time_Mins']).any():
            return None, "Temps d'arrêt supérieur au temps planifié."
        if (df['Good_Count'] > df['Total_Count']).any():
            return None, "Good_Count ne peut pas dépasser Total_Count."
        if not (df['Total_Count'] % 1 == 0).all() or not (df['Good_Count'] % 1 == 0).all():
            return None, "Les compteurs de production doivent être des nombres entiers."

        df['Run_Time'] = df['Planned_Time_Mins'] - df['Downtime_Mins']
        df['Ideal_Time'] = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']) / 60.0
        total_planned = float(df['Planned_Time_Mins'].sum())
        total_run = float(df['Run_Time'].sum())
        total_ideal = float(df['Ideal_Time'].sum())
        total_good = float(df['Good_Count'].sum())
        total_count = float(df['Total_Count'].sum())

        availability = total_run / total_planned * 100.0
        performance = total_ideal / total_run * 100.0 if total_run > 0 else 0.0
        quality = total_good / total_count * 100.0 if total_count > 0 else 0.0
        oee = availability * performance * quality / 10000.0
        return {
            "availability": availability,
            "performance": performance,
            "quality": quality,
            "oee": oee,
            "records": int(len(df)),
            "performance_over_100_warning": performance > 100.0,
        }, None

    def generate_forecast(self, date_col, value_col, periods=3):
        try:
            from prophet import Prophet
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
