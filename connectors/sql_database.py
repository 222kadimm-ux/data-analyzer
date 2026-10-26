import polars as pl
import pandas as pd
from sqlalchemy import create_engine, text
from .base import BaseConnector

# قائمة الجداول المسموح بها (لا تشمل users لأسباب أمنية)
ALLOWED_TABLES = ["production_data", "sales_data"]

class SQLDatabaseConnector(BaseConnector):
    def __init__(self, db_url, table_name, limit=10000):
        self.db_url = db_url
        self.table_name = table_name
        self.limit = limit

    def load_data(self) -> pl.DataFrame:
        # 1. التحقق من الجدول
        if self.table_name not in ALLOWED_TABLES:
            raise ValueError(f"❌ الجدول غير مسموح: {self.table_name}. الجداول المسموحة: {', '.join(ALLOWED_TABLES)}")
        
        # 2. التحقق من الحد
        if not isinstance(self.limit, int) or self.limit <= 0:
            self.limit = 10000

        try:
            engine = create_engine(self.db_url)
            query = text(f"SELECT * FROM {self.table_name} LIMIT {self.limit}")
            df_pd = pd.read_sql(query, engine)
            return pl.from_pandas(df_pd)
        except Exception as e:
            # عدم كشف الرابط أو كلمة المرور
            raise ValueError("❌ فشل الاتصال بقاعدة البيانات. تحقق من الصلاحيات.")
        finally:
            engine.dispose()
