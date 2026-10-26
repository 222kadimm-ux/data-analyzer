import polars as pl
import pandas as pd
import requests
from .base import BaseConnector

class RESTAPIConnector(BaseConnector):
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers or {}

    def load_data(self) -> pl.DataFrame:
        try:
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            # إذا كانت البيانات قائمة من القواميس
            if isinstance(data, list):
                return pl.from_pandas(pd.DataFrame(data))
            elif isinstance(data, dict) and 'data' in data:
                return pl.from_pandas(pd.DataFrame(data['data']))
            else:
                raise ValueError("صيغة JSON غير مدعومة")
        except Exception as e:
            raise ValueError(f"❌ فشل الاتصال بـ API: {e}")
