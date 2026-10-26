import pytest
import polars as pl
from connectors.csv_excel import CSVExcelConnector

class MockFile:
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.size = len(content)

def test_csv_connector_valid():
    # اختبار ملف CSV بسيط
    csv_content = b"Date,Sales\n2026-01-01,100\n2026-01-02,200"
    mock_file = MockFile("test.csv", csv_content)
    connector = CSVExcelConnector(mock_file)
    df = connector.load_data()
    assert df.height == 2
    assert df.columns == ["Date", "Sales"]

def test_csv_connector_too_large():
    # اختبار ملف كبير جداً
    mock_file = MockFile("large.csv", b"x" * 101 * 1024 * 1024) # 101 ميجابايت
    connector = CSVExcelConnector(mock_file)
    with pytest.raises(ValueError, match="الحد الأقصى"):
        connector.load_data()
