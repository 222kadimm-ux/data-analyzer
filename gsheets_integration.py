import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def load_from_google_sheets():
    """
    تتصل بـ Google Sheets وتقرأ البيانات منها.
    """
    if "gcp_service_account" not in st.secrets:
        st.error("⚠️ مفاتيح Google Sheets غير موجودة في إعدادات الأسرار.")
        return None
    
    try:
        # قراءة المفاتيح من secrets
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)

        # طلب رابط الشيت من المستخدم
        sheet_url = st.text_input("أدخل رابط Google Sheet (تأكد من مشاركته مع بريد البوت):")
        
        if st.button("سحب البيانات"):
            if sheet_url:
                with st.spinner("جارٍ سحب البيانات..."):
                    sheet = client.open_by_url(sheet_url).sheet1
                    data = sheet.get_all_records()
                    df = pd.DataFrame(data)
                    if df.empty:
                        st.warning("الشيت فارغ!")
                        return None
                    return df
            else:
                st.warning("الرجاء إدخال الرابط.")
                
    except gspread.exceptions.APIError:
        st.error("❌ خطأ في الصلاحيات: تأكد من مشاركة الشيت مع بريد البوت (Service Account).")
    except Exception as e:
        st.error(f"❌ حدث خطأ: {e}")
    
    return None
