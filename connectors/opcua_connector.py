import asyncio
import polars as pl
import pandas as pd
from asyncua import Client
from .base import BaseConnector

class OPCUAConnector(BaseConnector):
    def __init__(self, url, node_ids):
        self.url = url
        self.node_ids = node_ids

    async def _fetch_data(self):
        data = []
        # إضافة مهلة للاتصال (10 ثوانٍ)
        async with Client(url=self.url, timeout=10) as client:
            for node_id in self.node_ids:
                try:
                    node = client.get_node(node_id)
                    value = await node.read_value()
                    data.append({"NodeID": node_id, "Value": value})
                except Exception as e:
                    # رفض النتيجة إذا فشلت قراءة أي عقدة
                    raise ValueError(f"فشل قراءة العقدة {node_id}: {e}")
        return data

    def load_data(self) -> pl.DataFrame:
        try:
            data = asyncio.run(self._fetch_data())
            if not data:
                raise ValueError("لم يتم جلب أي بيانات من OPC UA.")
            
            # التحقق من وجود أي خطأ في البيانات
            for row in data:
                if "Error" in str(row.get("Value", "")):
                    raise ValueError(f"❌ فشل قراءة العقدة: {row['Value']}")
                    
            return pl.from_pandas(pd.DataFrame(data))
        except Exception as e:
            raise ValueError(f"❌ فشل الاتصال بـ OPC UA: {e}")
