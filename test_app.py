import pytest
import polars as pl
from core_engine import DataEngine
from validation.schema import SchemaValidator
from connectors.csv_excel import CSVExcelConnector

# ==========================================
# 1. اختبارات محرك OEE
# ==========================================

def test_calculate_oee_valid():
    df = pl.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [30],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [1500],
        'Good_Count': [1450]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    
    assert error is None
    assert result is not None
    assert result['availability'] == pytest.approx(93.75, 0.1)
    assert result['quality'] == pytest.approx(96.66, 0.1)

def test_oee_zero_planned_time():
    df = pl.DataFrame({
        'Planned_Time_Mins': [0],
        'Downtime_Mins': [0],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [0],
        'Good_Count': [0]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    assert result is None
    assert "الوقت المخطط يجب أن يكون أكبر من صفر" in error

def test_oee_zero_run_time():
    df = pl.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [480],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [1500],
        'Good_Count': [1450]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    assert result is None
    assert "توقف كامل" in error

def test_oee_negative_values():
    df = pl.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [-30],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [1500],
        'Good_Count': [1450]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    assert result is None
    assert "قيم سالبة" in error

def test_oee_good_count_exceeds_total():
    df = pl.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [30],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [1500],
        'Good_Count': [1600]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    assert result is None
    assert "عدد القطع السليمة أكبر من إجمالي القطع" in error

# ==========================================
# 2. اختبارات التحقق من المخطط (Schema)
# ==========================================

def test_validate_oee_columns_valid():
    df = pl.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [30],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [1500],
        'Good_Count': [1450]
    })
    validator = SchemaValidator(df)
    is_valid, msg = validator.validate_oee_columns()
    assert is_valid is True
    assert "موجودة" in msg

def test_validate_oee_columns_missing():
    df = pl.DataFrame({'Date': ['2026-01-01'], 'Sales': [100]})
    validator = SchemaValidator(df)
    is_valid, msg = validator.validate_oee_columns()
    assert is_valid is False
    assert "مفقودة" in msg

def test_validate_date_column_missing():
    df = pl.DataFrame({'Sales': [100, 200]})
    validator = SchemaValidator(df)
    is_valid, msg = validator.validate_date_column()
    assert is_valid is False
    assert "عمود تاريخ" in msg

# ==========================================
# 3. اختبارات موصل CSV/Excel
# ==========================================

class MockFile:
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.size = len(content)
        
    def read(self, *args, **kwargs):
        return self.content

def test_csv_connector_valid():
    csv_content = b"Date,Sales\n2026-01-01,100\n2026-01-02,200"
    mock_file = MockFile("test.csv", csv_content)
    connector = CSVExcelConnector(mock_file)
    df = connector.load_data()
    assert df.height == 2
    assert df.columns == ["Date", "Sales"]

def test_csv_connector_too_large():
    mock_file = MockFile("large.csv", b"x" * 101 * 1024 * 1024)
    connector = CSVExcelConnector(mock_file)
    with pytest.raises(ValueError, match="الحد الأقصى"):
        connector.load_data()
