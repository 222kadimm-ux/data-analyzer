import time
import streamlit as st
from asyncua import Client, ua

class OPCUAConnector:
    def __init__(self, url, node_id):
        self.url = url
        self.node_id = node_id
        self.client = None

    def connect(self):
        """الاتصال بالخادم مع إعادة المحاولة"""
        try:
            self.client = Client(url=self.url, timeout=10)
            self.client.connect()
            return True, "✅ Connecté au serveur OPC UA"
        except Exception as e:
            return False, f"❌ Échec de connexion: {e}"

    def read_value(self):
        """قراءة قيمة واحدة من العقدة"""
        if not self.client:
            return None, "❌ Non connecté"
        try:
            node = self.client.get_node(self.node_id)
            value = node.read_value()
            return value, "✅"
        except Exception as e:
            return None, f"❌ Erreur de lecture: {e}"

    def disconnect(self):
        """قطع الاتصال بأمان"""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass
            self.client = None

    def start_streaming(self, duration_sec=60, interval_sec=1):
        """بث مستمر للبيانات لمدة محددة (محاكاة لقراءة مستمرة)"""
        st.info(f"🔄 Démarrage du streaming pour {duration_sec} secondes...")
        data = []
        end_time = time.time() + duration_sec
        
        while time.time() < end_time:
            value, status = self.read_value()
            if value is not None:
                data.append({"timestamp": time.time(), "value": value})
                st.toast(f"Valeur: {value} (Total: {len(data)})")
            time.sleep(interval_sec)
        
        st.success(f"✅ Streaming terminé. {len(data)} valeurs lues.")
        return data
