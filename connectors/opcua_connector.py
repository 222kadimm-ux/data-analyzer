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
        # محاولة الاتصال بالخادم الحقيقي
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
            data = asyncio.run(self._fetch_data())
            if not data:
                raise ValueError("لم يتم جلب أي بيانات من OPC UA.")
            return pl.from_pandas(pd.DataFrame(data))
        except Exception as e:
            raise ValueError(f"❌ فشل الاتصال بـ OPC UA: {e}")
