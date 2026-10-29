import asyncio
import psycopg2
import os
from datetime import datetime
from asyncua import Client
from settings import DATABASE_URL

# إعدادات الآلة
OPC_URL = "opc.tcp://opcuademo.sterfive.com:26543"
NODE_ID = "ns=0;i=2258" # وقت الخادم (كمثال)

async def monitor():
    # 1. الاتصال بالآلة
    async with Client(url=OPC_URL) as client:
        node = client.get_node(NODE_ID)
        value = await node.read_value()
        
    # 2. حفظ في قاعدة البيانات
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO machine_logs (timestamp, machine_name, value) VALUES (%s, %s, %s)",
            (datetime.now(), "Machine_1", str(value))
        )
        conn.commit()
        print(f"✅ Logged: {value}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    asyncio.run(monitor())
