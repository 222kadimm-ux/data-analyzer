from abc import ABC, abstractmethod
import polars as pl

class BaseConnector(ABC):
    @abstractmethod
    def load_data(self) -> pl.DataFrame:
        """يجب على كل موصل تنفيذ هذه الدالة لإرجاع DataFrame"""
        pass
