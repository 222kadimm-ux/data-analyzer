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
    assert round(result['availability'], 2) == 0.94

def test_calculate_oee_missing_columns():
    df = pl.DataFrame({
        'Product': ['A', 'B'],
        'Sales': [100, 200]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    
    assert result is None
    assert error is not None
