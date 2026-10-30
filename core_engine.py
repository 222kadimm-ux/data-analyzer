
import polars as pl
import pandas as pd
import numpy as np


class DataEngine:
    def __init__(self, df_polars):
        if not isinstance(df_polars, pl.DataFrame):
            raise TypeError(
                "DataEngine requires a Polars DataFrame."
            )

        self.df = df_polars

    def get_basic_stats(self):
        """Return basic dataset statistics."""

        numeric_cols = [
            col
            for col, dtype in zip(
                self.df.columns,
                self.df.dtypes
            )
            if dtype.is_numeric()
        ]

        total = 0.0

        if numeric_cols and self.df.height > 0:
            value = self.df[numeric_cols[0]].sum()

            total = (
                float(value)
                if value is not None
                else 0.0
            )

            if not np.isfinite(total):
                total = 0.0

        stats = {
            "records": int(self.df.height),
            "total": total,
            "columns": int(self.df.width),
            "numeric_columns": len(numeric_cols),
        }

        if self.df.height > 0 and self.df.width > 0:
            pdf = self.df.to_pandas()

            stats["missing_values"] = int(
                pdf.isna().sum().sum()
            )

            stats["duplicate_rows"] = int(
                pdf.duplicated().sum()
            )
        else:
            stats["missing_values"] = 0
            stats["duplicate_rows"] = 0

        return stats

    def calculate_oee(self):
        """
        Calculate industrial OEE.

        Availability = Run Time / Planned Time
        Performance = Ideal Production Time / Run Time
        Quality = Good Count / Total Count

        OEE = Availability * Performance * Quality
        """

        if self.df.height == 0:
            return None, (
                "لا يمكن حساب OEE لأن جدول البيانات فارغ."
            )

        required_columns = [
            "Planned_Time_Mins",
            "Downtime_Mins",
            "Ideal_Cycle_Time_Sec",
            "Total_Count",
            "Good_Count",
        ]

        missing = [
            col
            for col in required_columns
            if col not in self.df.columns
        ]

        if missing:
            return None, (
                "Colonnes OEE manquantes: "
                + ", ".join(missing)
            )

        try:
            df = self.df.to_pandas().copy()

            for col in required_columns:
                df[col] = pd.to_numeric(
                    df[col],
                    errors="raise"
                )

        except (TypeError, ValueError):
            return None, (
                "Les colonnes OEE doivent contenir "
                "uniquement des nombres."
            )

        values = df[required_columns].to_numpy(
            dtype=float
        )

        if not np.isfinite(values).all():
            return None, (
                "Valeurs manquantes ou non finies "
                "dans les colonnes OEE."
            )

        if (df[required_columns] < 0).any().any():
            return None, "Valeurs négatives détectées."

        if (df["Ideal_Cycle_Time_Sec"] <= 0).any():
            return None, (
                "Ideal_Cycle_Time_Sec doit être "
                "strictement positif."
            )

        if (df["Planned_Time_Mins"] <= 0).any():
            return None, (
                "Planned_Time_Mins doit être "
                "strictement positif."
            )

        if (
            df["Downtime_Mins"]
            > df["Planned_Time_Mins"]
        ).any():
            return None, (
                "Temps d'arrêt supérieur "
                "au temps planifié."
            )

        if (
            df["Good_Count"] > df["Total_Count"]
        ).any():
            return None, (
                "Good_Count ne peut pas dépasser Total_Count."
            )

        if not (
            df["Total_Count"] % 1 == 0
        ).all():
            return None, (
                "Total_Count doit contenir "
                "des nombres entiers."
            )

        if not (
            df["Good_Count"] % 1 == 0
        ).all():
            return None, (
                "Good_Count doit contenir "
                "des nombres entiers."
            )

        df["Run_Time"] = (
            df["Planned_Time_Mins"]
            - df["Downtime_Mins"]
        )

        df["Ideal_Time"] = (
            df["Total_Count"]
            * df["Ideal_Cycle_Time_Sec"]
            / 60.0
        )

        total_planned = float(
            df["Planned_Time_Mins"].sum()
        )

        total_run = float(
            df["Run_Time"].sum()
        )

        total_ideal = float(
            df["Ideal_Time"].sum()
        )

        total_good = float(
            df["Good_Count"].sum()
        )

        total_count = float(
            df["Total_Count"].sum()
        )

        if total_planned <= 0:
            return None, (
                "Total planned time must be positive."
            )

        availability = (
            total_run / total_planned
        ) * 100.0

        performance = (
            (total_ideal / total_run) * 100.0
            if total_run > 0
            else 0.0
        )

        quality = (
            (total_good / total_count) * 100.0
            if total_count > 0
            else 0.0
        )

        oee = (
            availability
            * performance
            * quality
            / 10000.0
        )

        result = {
            "availability": availability,
            "performance": performance,
            "quality": quality,
            "oee": oee,
            "records": int(len(df)),
            "performance_over_100_warning": (
                performance > 100.0
            ),
        }

        return result, None

    def generate_forecast(
        self,
        date_col,
        value_col,
        periods=3,
        freq="ME"
    ):
        """Generate a Prophet forecast."""

        try:
            from prophet import Prophet

            if (
                date_col not in self.df.columns
                or value_col not in self.df.columns
            ):
                return None, None, (
                    "Colonne Date ou valeur introuvable."
                )

            try:
                periods = int(periods)
            except (TypeError, ValueError):
                return None, None, (
                    "Le nombre de périodes doit être un entier."
                )

            if periods < 1 or periods > 365:
                return None, None, (
                    "Le nombre de périodes doit être "
                    "compris entre 1 et 365."
                )

            prophet_df = self.df.to_pandas()[
                [date_col, value_col]
            ].copy()

            prophet_df.columns = ["ds", "y"]

            prophet_df["ds"] = pd.to_datetime(
                prophet_df["ds"],
                errors="coerce"
            )

            prophet_df["y"] = pd.to_numeric(
                prophet_df["y"],
                errors="coerce"
            )

            prophet_df = prophet_df.replace(
                [np.inf, -np.inf],
                np.nan
            ).dropna(subset=["ds", "y"])

            prophet_df = (
                prophet_df
                .groupby("ds", as_index=False)["y"]
                .mean()
                .sort_values("ds")
            )

            if len(prophet_df) < 2:
                return None, None, (
                    "Besoin d'au moins 2 points "
                    "de données valides."
                )

            if prophet_df["y"].nunique() < 2:
                return None, None, (
                    "Les valeurs sont constantes. "
                    "Une prévision fiable est impossible."
                )

            model = Prophet()
            model.fit(prophet_df)

            future = model.make_future_dataframe(
                periods=periods,
                freq=freq
            )

            forecast = model.predict(future)

            return model, forecast, None

        except Exception as exc:
            return None, None, (
                f"Échec de la prévision : {exc}"
            )

    def get_correlation_matrix(self):
        """Return correlation matrix for numeric columns."""

        if self.df.height == 0:
            return None

        df = self.df.to_pandas()

        numeric_df = df.select_dtypes(
            include=["number"]
        )

        if len(numeric_df.columns) < 2:
            return None

        return numeric_df.corr()
