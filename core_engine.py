import polars as pl
import pandas as pd

class DataEngine:
    def __init__(self, df_polars):
        self.df = df_polars

    def get_basic_stats(self):
        numeric_cols = [c for c in self.df.columns if self.df[c].dtype in [pl.Float64, pl.Int64]]
        if not numeric_cols:
            return {"records": self.df.height, "total": 0, "top_item": "N/A"}
        total = self.df[numeric_cols[0]].sum()
        return {"records": self.df.height, "total": total}

    def calculate_oee(self):
        df = self.df.to_pandas()
        req = ['Planned_Time_Mins', 'Downtime_Mins', 'Ideal_Cycle_Time_Sec', 'Total_Count', 'Good_Count']
        if not all(c in df.columns for c in req):
            return None, "Colonnes OEE manquantes"
        
        try:
            # 1. التحقق من القيم السالبة
            if (df[req] < 0).any().any():
                return None, "⚠️ البيانات تحتوي على قيم سالبة. يرجى تصحيح الملف."

            # 2. منع القسمة على صفر
            df['Run_Time'] = df['Planned_Time_Mins'] - df['Downtime_Mins']
            df['Run_Time'] = df['Run_Time'].replace(0, 1) 
            
            df['Availability'] = df['Run_Time'] / df['Planned_Time_Mins']
            
            df['Ideal_Time'] = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']) / 60
            df['Performance'] = df['Ideal_Time'] / df['Run_Time']
            
            df['Quality'] = df['Good_Count'] / df['Total_Count'].replace(0, 1)
            
            df['OEE'] = df['Availability'] * df['Performance'] * df['Quality']
            
            # 3. التحقق من المنطقية
            perf = df['Performance'].mean() * 100
            warning = None
            if perf < 50:
                warning = "⚠️ الأداء منخفض جداً (أقل من 50%). يرجى التأكد من أن العمود 'Ideal_Cycle_Time_Sec' بالثواني، وأن 'Total_Count' يعكس الإنتاج الفعلي."
            if df['OEE'].mean() > 100:
                warning = "⚠️ OEE أكبر من 100% (غير منطقي). تأكد من أن Planned_Time_Mins أكبر من Downtime_Mins."
            
            result = {
                "availability": df['Availability'].mean() * 100,
                "performance": perf,
                "quality": df['Quality'].mean() * 100,
                "oee": df['OEE'].mean() * 100,
                "warning": warning
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

def fetch_shopify_data(shop_url, api_key, password):
    import shopify
    try:
        session = shopify.Session(shop_url, '2024-01', password)
        shopify.ShopifyResource.activate_session(session)
        orders = shopify.Order.find(limit=50)
        data = []
        for order in orders:
            data.append({
                'Date': order.created_at,
                'Total_Price': float(order.total_price),
                'Customer_Email': order.email,
                'Order_ID': order.id
            })
        shopify.ShopifyResource.clear_session()
        return pl.from_pandas(pd.DataFrame(data)) if data else None
    except: return None
