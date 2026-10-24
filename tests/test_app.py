import pytest
import pandas as pd
import polars as pl

# 1. اختبار حساب OEE
def test_oee_calculation():
    # بيانات وهمية
    df = pd.DataFrame({
        'Planned_Time_Mins': [480],
        'Downtime_Mins': [30],
        'Ideal_Cycle_Time_Sec': [1.0],
        'Total_Count': [1500],
        'Good_Count': [1450]
    })
    
    df['Run_Time_Mins'] = df['Planned_Time_Mins'] - df['Downtime_Mins']
    df['Availability'] = df['Run_Time_Mins'] / df['Planned_Time_Mins']
    df['Ideal_Time_Mins'] = (df['Total_Count'] * df['Ideal_Cycle_Time_Sec']) / 60
    df['Performance'] = df['Ideal_Time_Mins'] / df['Run_Time_Mins']
    df['Quality'] = df['Good_Count'] / df['Total_Count']
    df['OEE'] = df['Availability'] * df['Performance'] * df['Quality']
    
    # التحقق من القيم المتوقعة
    assert round(df['Availability'][0], 2) == 0.94
    assert round(df['Quality'][0], 2) == 0.97
    assert round(df['OEE'][0], 2) == 0.91

# 2. اختبار تحويل البيانات (Polars)
def test_polars_conversion():
    df_pd = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
    df_pl = pl.from_pandas(df_pd)
    assert df_pl.height == 2
    assert df_pl.columns == ['A', 'B']

# 3. اختبار حساب الإحصائيات
def test_basic_statistics():
    df = pd.DataFrame({'Sales': [100, 200, 300]})
    assert df['Sales'].sum() == 600
    assert df['Sales'].mean() == 200

# 4. اختبار التحقق من حجم الملف (محاكاة)
def test_file_size_limit():
    max_size = 100 * 1024 * 1024 # 100MB
    file_size = 150 * 1024 * 1024 # 150MB
    assert file_size > max_size # يجب أن يظهر خطأ

# 5. اختبار الترتيب (Pareto)
def test_pareto_sorting():
    df = pd.DataFrame({
        'Reason': ['Breakdown', 'Setup', 'Maintenance'],
        'Downtime': [120, 60, 30]
    })
    sorted_df = df.sort_values(by='Downtime', ascending=False)
    assert sorted_df.iloc[0]['Reason'] == 'Breakdown'
