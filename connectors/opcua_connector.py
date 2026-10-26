import asyncio
import polars as pl
import pandas as pd
from asyncua import Client
from .base import BaseConnector

class OPCUAConnector(BaseConnector):
    def __init__(self, url, node_ids):
        self.url = url
        # هذه هي العناوين (Node IDs) التي سنقرأ منها البيانات
        # استخدمنا عنواناً حقيقياً من السيرفر العام (nsu=http://test.org/UA/Data/;i=10854) 
        self.node_ids = node_ids 

    async def _fetch_data(self):
        data = []
        # الاتصال بالسيرفر
        async with Client(url=self.url) as client:
            for node_id in self.node_ids:
                try:
                    node = client.get_node(node_id)
                    value = await node.read_value()
                    data.append({"NodeID": node_id, "Value": value})
                except Exception as e:
                    data.append({"NodeID": node_id, "Value": f"Error: {e}"})
        return data

    def load_data(self) -> pl.DataFrame:
        try:
            # تشغيل الكود غير المتزامن
            data = asyncio.run(self._fetch_data())
            if not data:
                raise ValueError("لم يتم جلب أي بيانات.")
            return pl.from_pandas(pd.DataFrame(data))
        except Exception as e:
            raise ValueError(f"❌ فشل الاتصال بـ OPC UA: {e}")
