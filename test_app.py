import pytest
import polars as pl
from core_engine import DataEngine

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
    # التحقق من الإتاحة بدقة (القيمة الحقيقية هي 93.75%)
    assert result['availability'] == pytest.approx(93.75, 0.1)
    # التحقق من الجودة (1450/1500 = 96.66%)
    assert result['quality'] == pytest.approx(96.66, 0.1)

def test_calculate_oee_missing_columns():
    df = pl.DataFrame({
        'Product': ['A', 'B'],
        'Sales': [100, 200]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    
    assert result is None
    assert error is not None
