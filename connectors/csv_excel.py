import polars as pl
import pandas as pd
from .base import BaseConnector
import streamlit as st

class CSVExcelConnector(BaseConnector):
    def __init__(self, uploaded_file):
        self.file = uploaded_file

    def load_data(self) -> pl.DataFrame:
        if self.file.size > 100 * 1024 * 1024:
            raise ValueError("🚫 الملف كبير جداً! الحد الأقصى 100 ميجابايت.")
        
        try:
            if self.file.name.endswith('.csv'):
                df = pl.read_csv(self.file, infer_schema_length=10000, ignore_errors=True)
            else:
                df = pl.read_excel(self.file)
            return df
        except Exception as e:
            raise ValueError(f"❌ خطأ في قراءة الملف: {e}")
