from __future__ import annotations

import polars as pl
from .base import BaseConnector


class CSVExcelConnector(BaseConnector):
    def __init__(self, uploaded_file):
        self.file = uploaded_file

    def load_data(self) -> pl.DataFrame:
        file_name = str(getattr(self.file, "name", "")).lower()
        file_size = getattr(self.file, "size", None)
        if file_size is not None and file_size > 100 * 1024 * 1024:
            raise ValueError("🚫 Fichier trop volumineux : limite de 100 Mo.")
        if not file_name.endswith((".csv", ".xlsx", ".xls", ".xlsb", ".ods")):
            raise ValueError("Format non pris en charge. Utilisez un fichier CSV ou Excel.")

        try:
            if hasattr(self.file, "seek"):
                self.file.seek(0)
            if file_name.endswith(".csv"):
                df = pl.read_csv(self.file, infer_schema_length=10000, try_parse_dates=True)
            else:
                df = pl.read_excel(self.file)
            if df.height == 0:
                raise ValueError("Le fichier ne contient aucune ligne de données.")
            if df.width == 0:
                raise ValueError("Le fichier ne contient aucune colonne exploitable.")
            if hasattr(self.file, "seek"):
                self.file.seek(0)
            return df
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"❌ Impossible de lire le fichier : {exc}") from exc
