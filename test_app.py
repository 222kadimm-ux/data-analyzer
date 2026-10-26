import pytest
import polars as pl
from core_engine import DataEngine
from quality_checker import DataQualityChecker

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
        'Downtime_Mins': [480], # توقف كامل
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [1500],
        'Good_Count': [1450]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    # يجب ألا ينهار، بل يعيد 0
    assert error is None
    assert result['oee'] == 0
    assert "وقت تشغيل صفر" in result['warning']

def test_quality_checker_negative():
    df = pl.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [-30],
        'Total_Count': [1500],
        'Good_Count': [1450]
    })
    checker = DataQualityChecker(df)
    report, issues = checker.get_report()
    assert any("سالبة" in issue for issue in issues)
