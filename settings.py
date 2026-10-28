import os
import streamlit as st

def get_secret(key, default=None):
    # 1. البحث في متغيرات البيئة أولاً
    if key in os.environ:
        return os.environ[key]
    # 2. البحث في st.secrets
    try:
        return st.secrets[key]
    except:
        return default

DATABASE_URL = get_secret("DATABASE_URL")
OPENROUTER_API_KEY = get_secret("OPENROUTER_API_KEY")
SENTRY_DSN = get_secret("SENTRY_DSN")
