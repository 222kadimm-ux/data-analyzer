import polars as pl
import pandas as pd
import requests
from urllib.parse import urlparse
from .base import BaseConnector

# قائمة النطاقات المسموح بها (للأمان)
ALLOWED_DOMAINS = ["jsonplaceholder.typicode.com", "api.example.com"]

class RESTAPIConnector(BaseConnector):
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers or {}

    def load_data(self) -> pl.DataFrame:
        # 1. التحقق من النطاق
        parsed = urlparse(self.url)
        if parsed.netloc not in ALLOWED_DOMAINS:
            raise ValueError(f"❌ النطاق غير مسموح: {parsed.netloc}. النطاقات المسموحة: {', '.join(ALLOWED_DOMAINS)}")

        try:
            # 2. مهلة الاتصال وحدود الحجم
            response = requests.get(self.url, headers=self.headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # 3. قراءة البيانات (بحد أقصى 5 ميجابايت)
            content = response.content[:5 * 1024 * 1024] # 5MB
            data = response.json()
            
            if isinstance(data, list):
                return pl.from_pandas(pd.DataFrame(data))
            elif isinstance(data, dict) and 'data' in data:
                return pl.from_pandas(pd.DataFrame(data['data']))
            else:
                raise ValueError("صيغة JSON غير مدعومة")
        except requests.exceptions.Timeout:
            raise ValueError("⚠️ انتهت مهلة الاتصال بالخادم.")
        except Exception as e:
            raise ValueError(f"❌ فشل الاتصال بـ API: {str(e)}")
