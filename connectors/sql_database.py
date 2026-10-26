import polars as pl
import pandas as pd
from sqlalchemy import create_engine, text
from .base import BaseConnector

class SQLDatabaseConnector(BaseConnector):
    def __init__(self, db_url, table_name, limit=10000):
        self.db_url = db_url
        self.table_name = table_name
        self.limit = limit

    def load_data(self) -> pl.DataFrame:
        # تأمين اسم الجدول
        if not self.table_name.isalnum():
            raise ValueError("❌ اسم الجدول غير آمن (يجب أن يكون حروفاً وأرقاماً فقط).")
        
        try:
            engine = create_engine(self.db_url)
            query = text(f"SELECT * FROM {self.table_name} LIMIT {self.limit}")
            df_pd = pd.read_sql(query, engine)
            return pl.from_pandas(df_pd)
        except Exception as e:
            raise ValueError(f"❌ فشل الاتصال بقاعدة البيانات: {e}")
