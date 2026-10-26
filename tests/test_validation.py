import pytest
import polars as pl
from validation.schema import SchemaValidator

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
