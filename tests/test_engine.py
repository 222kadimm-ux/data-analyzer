import pytest
import polars as pl
from core_engine import DataEngine

# اختبار 1: حساب OEE لبيانات صحيحة
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
    assert round(result['quality'], 2) == 0.97

# اختبار 2: حساب OEE لبيانات ناقصة (يجب أن يعيد خطأ)
def test_calculate_oee_missing_columns():
    df = pl.DataFrame({
        'Product': ['A', 'B'],
        'Sales': [100, 200]
    })
    engine = DataEngine(df)
    result, error = engine.calculate_oee()
    
    assert result is None
    assert error is not None
    assert "manquantes" in error # يجب أن يحتوي الخطأ على كلمة "مفقودة"

# اختبار 3: الإحصائيات الأساسية
def test_basic_stats():
    df = pl.DataFrame({
        'Sales': [100, 200, 300]
    })
    engine = DataEngine(df)
    stats = engine.get_basic_stats()
    
    assert stats['records'] == 3
    assert stats['total'] == 600
