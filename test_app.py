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
    
    assert result['availability'] == pytest.approx(93.75, 0.1)
    assert result['quality'] == pytest.approx(96.66, 0.1)
    
    expected_perf = (1500 * 1.0) / 60 / 450 * 100
    assert result['performance'] == pytest.approx(expected_perf, 0.1)
    
    expected_oee = (93.75 / 100) * (expected_perf / 100) * (96.66 / 100) * 100
    assert result['oee'] == pytest.approx(expected_oee, 0.1)

def test_calculate_oee_missing_columns():
    df = pl.DataFrame({
        'Product': ['A', 'B'],
        'Sales': [100, 200]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    
    assert result is None
    assert error is not None

def test_oee_division_by_zero():
    df = pl.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [480],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [0],
        'Good_Count': [0]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    assert error is None
    assert result['oee'] == 0
