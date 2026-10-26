import polars as pl

class SchemaValidator:
    def __init__(self, df: pl.DataFrame):
        self.df = df

    def validate_oee_columns(self) -> tuple[bool, str]:
        """التحقق من وجود أعمدة OEE"""
        required = ['Planned_Time_Mins', 'Downtime_Mins', 'Ideal_Cycle_Time_Sec', 'Total_Count', 'Good_Count']
        missing = [col for col in required if col not in self.df.columns]
        if missing:
            return False, f"⚠️ الأعمدة التالية مفقودة: {', '.join(missing)}"
        return True, "✅ جميع أعمدة OEE موجودة."

    def validate_date_column(self) -> tuple[bool, str]:
        """التحقق من وجود عمود تاريخ"""
        date_cols = [c for c in self.df.columns if 'date' in c.lower() or 'mois' in c.lower()]
        if not date_cols:
            return False, "⚠️ لا يوجد عمود تاريخ. التنبؤ الزمني لن يعمل."
        return True, f"✅ عمود التاريخ موجود: {date_cols[0]}"

    def validate_numeric_columns(self) -> tuple[bool, str]:
        """التحقق من وجود أعمدة رقمية"""
        numeric_cols = [c for c in self.df.columns if self.df[c].dtype in [pl.Float64, pl.Int64]]
        if not numeric_cols:
            return False, "⚠️ لا توجد أعمدة رقمية. لا يمكن إجراء التحليل."
        return True, f"✅ توجد {len(numeric_cols)} أعمدة رقمية."
