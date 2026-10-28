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


def test_sql_query_validator_accepts_only_selected_table():
    from connectors.sql_database import validate_simple_select
    safe = validate_simple_select("SELECT id, amount FROM production_data WHERE amount > 10", "production_data")
    assert safe.endswith("LIMIT 1000")


def test_sql_query_validator_rejects_multiple_statements():
    from connectors.sql_database import validate_simple_select
    with pytest.raises(ValueError):
        validate_simple_select("SELECT * FROM production_data; DROP TABLE users", "production_data")


def test_sql_query_validator_rejects_other_table():
    from connectors.sql_database import validate_simple_select
    with pytest.raises(ValueError):
        validate_simple_select("SELECT * FROM users", "production_data")
