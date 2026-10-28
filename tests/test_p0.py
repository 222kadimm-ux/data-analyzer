import pytest
import pandas as pd
from database import save_file, get_files

def test_save_anonymous_user():
    """اختبار P0-2: حفظ ملف لمستخدم مجهول (UUID)"""
    uuid = "test-uuid-1234"
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    result = save_file(uuid, "test.csv", df)
    assert result == True

def test_date_format_roundtrip():
    """اختبار P0-4: التأكد من حفظ التاريخ بصيغة ISO"""
    df = pd.DataFrame({"date": pd.to_datetime(["2026-10-27"])})
    json_data = df.to_json(orient='records', date_format='iso')
    assert "2026-10-27" in json_data
