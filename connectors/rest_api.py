import polars as pl
import pandas as pd
import requests
from urllib.parse import urlparse
from .base import BaseConnector

# قائمة النطاقات المسموح بها
ALLOWED_DOMAINS = ["jsonplaceholder.typicode.com", "dummyjson.com"]

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
            # 2. جلب البيانات
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # 3. البحث التلقائي عن القائمة داخل الاستجابة
            if isinstance(data, list):
                # إذا كانت الاستجابة قائمة مباشرة
                return pl.from_pandas(pd.DataFrame(data))
            elif isinstance(data, dict):
                # إذا كانت قاموساً، نبحث عن أول قيمة هي قائمة
                for key, value in data.items():
                    if isinstance(value, list):
                        return pl.from_pandas(pd.DataFrame(value))
                # إذا لم نجد قائمة، نأخذ القاموس نفسه كصف واحد
                return pl.from_pandas(pd.DataFrame([data]))
            else:
                raise ValueError("صيغة JSON غير مدعومة")
                
        except requests.exceptions.Timeout:
            raise ValueError("⚠️ انتهت مهلة الاتصال بالخادم.")
        except Exception as e:
            raise ValueError(f"❌ فشل الاتصال بـ API: {str(e)}")
