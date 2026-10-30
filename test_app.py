
import pytest
import polars as pl

from core_engine import DataEngine
from validation.schema import SchemaValidator
from connectors.csv_excel import CSVExcelConnector
from quality_checker import DataQualityChecker


# ==========================================
# 1. OEE ENGINE TESTS
# ==========================================

def test_calculate_oee_valid():
    df = pl.DataFrame({
        "Planned_Time_Mins": [480],
        "Downtime_Mins": [30],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [1500],
        "Good_Count": [1450],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert error is None
    assert result is not None

    assert result["availability"] == pytest.approx(93.75)
    assert result["performance"] == pytest.approx(
        5.55555556
    )
    assert result["quality"] == pytest.approx(
        96.66666667
    )
    assert result["oee"] == pytest.approx(
        5.03472222
    )


def test_oee_empty_dataframe():
    df = pl.DataFrame({
        "Planned_Time_Mins": [],
        "Downtime_Mins": [],
        "Ideal_Cycle_Time_Sec": [],
        "Total_Count": [],
        "Good_Count": [],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert result is None
    assert error is not None
    assert "فارغ" in error


def test_oee_zero_planned_time():
    df = pl.DataFrame({
        "Planned_Time_Mins": [0],
        "Downtime_Mins": [0],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [0],
        "Good_Count": [0],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert result is None
    assert "strictement positif" in error


def test_oee_zero_run_time():
    df = pl.DataFrame({
        "Planned_Time_Mins": [480],
        "Downtime_Mins": [480],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [1500],
        "Good_Count": [1450],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert error is None
    assert result["availability"] == pytest.approx(0.0)
    assert result["performance"] == pytest.approx(0.0)
    assert result["oee"] == pytest.approx(0.0)


def test_oee_negative_values():
    df = pl.DataFrame({
        "Planned_Time_Mins": [480],
        "Downtime_Mins": [-30],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [1500],
        "Good_Count": [1450],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert result is None
    assert "négatives" in error


def test_oee_good_count_exceeds_total():
    df = pl.DataFrame({
        "Planned_Time_Mins": [480],
        "Downtime_Mins": [30],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [1500],
        "Good_Count": [1600],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert result is None
    assert "Good_Count" in error


def test_oee_missing_column():
    df = pl.DataFrame({
        "Planned_Time_Mins": [480],
        "Downtime_Mins": [30],
        "Total_Count": [1500],
        "Good_Count": [1450],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert result is None
    assert "Ideal_Cycle_Time_Sec" in error


def test_oee_performance_over_100_warning():
    df = pl.DataFrame({
        "Planned_Time_Mins": [100],
        "Downtime_Mins": [0],
        "Ideal_Cycle_Time_Sec": [10.0],
        "Total_Count": [1000],
        "Good_Count": [1000],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert error is None
    assert result is not None
    assert result["performance_over_100_warning"] is True


def test_oee_invalid_numeric_value():
    df = pl.DataFrame({
        "Planned_Time_Mins": ["invalid"],
        "Downtime_Mins": [30],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [1500],
        "Good_Count": [1450],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert result is None
    assert error is not None


def test_oee_nan_value():
    df = pl.DataFrame({
        "Planned_Time_Mins": [480.0],
        "Downtime_Mins": [30.0],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [1500.0],
        "Good_Count": [float("nan")],
    })

    engine = DataEngine(df)
    result, error = engine.calculate_oee()

    assert result is None
    assert "non finies" in error


# ==========================================
# 2. BASIC STATISTICS TESTS
# ==========================================

def test_basic_stats_empty_dataframe():
    df = pl.DataFrame()

    engine = DataEngine(df)
    result = engine.get_basic_stats()

    assert result["records"] == 0
    assert result["columns"] == 0
    assert result["missing_values"] == 0
    assert result["duplicate_rows"] == 0


def test_basic_stats_normal_dataframe():
    df = pl.DataFrame({
        "Production": [10, 20, 30],
        "Temperature": [25, 26, 27],
    })

    engine = DataEngine(df)
    result = engine.get_basic_stats()

    assert result["records"] == 3
    assert result["columns"] == 2
    assert result["numeric_columns"] == 2


# ==========================================
# 3. CORRELATION TESTS
# ==========================================

def test_correlation_matrix_valid():
    df = pl.DataFrame({
        "A": [1, 2, 3],
        "B": [2, 4, 6],
    })

    engine = DataEngine(df)
    result = engine.get_correlation_matrix()

    assert result is not None
    assert "A" in result.columns
    assert "B" in result.columns


def test_correlation_matrix_insufficient_columns():
    df = pl.DataFrame({
        "A": [1, 2, 3],
    })

    engine = DataEngine(df)
    result = engine.get_correlation_matrix()

    assert result is None


# ==========================================
# 4. SCHEMA VALIDATION TESTS
# ==========================================

def test_validate_oee_columns_valid():
    df = pl.DataFrame({
        "Planned_Time_Mins": [480],
        "Downtime_Mins": [30],
        "Ideal_Cycle_Time_Sec": [1.0],
        "Total_Count": [1500],
        "Good_Count": [1450],
    })

    validator = SchemaValidator(df)
    is_valid, msg = validator.validate_oee_columns()

    assert is_valid is True
    assert "موجودة" in msg


def test_validate_oee_columns_missing():
    df = pl.DataFrame({
        "Date": ["2026-01-01"],
        "Sales": [100],
    })

    validator = SchemaValidator(df)
    is_valid, msg = validator.validate_oee_columns()

    assert is_valid is False
    assert "مفقودة" in msg


def test_validate_date_column_missing():
    df = pl.DataFrame({
        "Sales": [100, 200],
    })

    validator = SchemaValidator(df)
    is_valid, msg = validator.validate_date_column()

    assert is_valid is False
    assert "عمود تاريخ" in msg


# ==========================================
# 5. DATA QUALITY TESTS
# ==========================================

def test_quality_empty_dataframe():
    df = pl.DataFrame()

    checker = DataQualityChecker(df)
    report, issues = checker.get_report()

    assert "الملف فارغ" in issues[0]


# ==========================================
# 6. CSV / EXCEL CONNECTOR TESTS
# ==========================================

class MockFile:
    def __init__(self, name, content):
        self.name = name
        self.content = content
        self.size = len(content)

    def read(self, *args, **kwargs):
        return self.content


def test_csv_connector_valid():
    csv_content = (
        b"Date,Sales\n"
        b"2026-01-01,100\n"
        b"2026-01-02,200"
    )

    mock_file = MockFile(
        "test.csv",
        csv_content
    )

    connector = CSVExcelConnector(mock_file)
    df = connector.load_data()

    assert df.height == 2
    assert df.columns == ["Date", "Sales"]


def test_csv_connector_too_large():
    mock_file = MockFile(
        "large.csv",
        b"x" * 101 * 1024 * 1024
    )

    connector = CSVExcelConnector(mock_file)

    with pytest.raises(
        ValueError,
        match="الحد الأقصى"
    ):
        connector.load_data()
