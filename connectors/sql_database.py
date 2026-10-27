import polars as pl
import pandas as pd
from sqlalchemy import create_engine, text
from urllib.parse import urlparse
from .base import BaseConnector

# قائمة المضيفين المسموح بهم (يجب تعديلها حسب بيئة الإنتاج)
ALLOWED_HOSTS = ["ep-purple-mud-b5sns22j-pooler.c-7.us-east-2.aws.neon.tech"]
ALLOWED_TABLES = ["production_data", "sales_data"]

class SQLDatabaseConnector(BaseConnector):
    def __init__(self, db_url, table_name, limit=10000):
        self.db_url = db_url
        self.table_name = table_name
        self.limit = limit

    def load_data(self) -> pl.DataFrame:
        # 1. التحقق من المضيف لمنع SSRF
        parsed = urlparse(self.db_url)
        if parsed.hostname not in ALLOWED_HOSTS:
            raise ValueError("❌ المضيف غير مسموح. اتصل بالدعم.")
            
        # 2. التحقق من الجدول
        if self.table_name not in ALLOWED_TABLES:
            raise ValueError("❌ الجدول غير مسموح.")
        
        # 3. التحقق من الحد
        if not isinstance(self.limit, int) or self.limit <= 0:
            self.limit = 10000

        try:
            engine = create_engine(self.db_url)
            query = text(f"SELECT * FROM {self.table_name} LIMIT {self.limit}")
            df_pd = pd.read_sql(query, engine)
            return pl.from_pandas(df_pd)
        except Exception:
            raise ValueError("❌ فشل الاتصال بقاعدة البيانات. تحقق من الصلاحيات.")
        finally:
            engine.dispose()
