import polars as pl
import pandas as pd
import requests
from urllib.parse import urlparse
from .base import BaseConnector

# قائمة النطاقات المسموح بها
ALLOWED_DOMAINS = ["jsonplaceholder.typicode.com", "dummyjson.com"]

class RESTAPIConnector(BaseConnector):
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers or {}

    def load_data(self) -> pl.DataFrame:
        parsed = urlparse(self.url)
        domain = (parsed.hostname or "").lower()
        if parsed.scheme not in {"https", "http"} or domain not in ALLOWED_DOMAINS:
            raise ValueError(
                f"❌ URL ou domaine non autorisé : {domain or 'inconnu'}. "
                f"Domaines autorisés : {', '.join(ALLOWED_DOMAINS)}"
            )

        try:
            response = requests.get(self.url, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                rows = data
            elif isinstance(data, dict):
                preferred_keys = ("data", "results", "items", "records", "users", "products")
                rows = None
                for key in preferred_keys:
                    value = data.get(key)
                    if isinstance(value, list):
                        rows = value
                        break
                if rows is None:
                    lists = [value for value in data.values() if isinstance(value, list)]
                    if len(lists) == 1:
                        rows = lists[0]
                    elif len(lists) > 1:
                        raise ValueError(
                            "La réponse contient plusieurs listes. Impossible de choisir automatiquement la bonne."
                        )
                    else:
                        rows = [data]
            else:
                raise ValueError("Format JSON non pris en charge : une liste ou un objet est attendu.")

            if not rows:
                raise ValueError("L'API a renvoyé une liste vide.")
            if not all(isinstance(row, dict) for row in rows):
                raise ValueError("La liste JSON doit contenir des objets pour former un tableau.")
            return pl.from_pandas(pd.DataFrame(rows))
        except requests.exceptions.Timeout as exc:
            raise ValueError("⚠️ Délai de connexion à l'API dépassé.") from exc
        except requests.exceptions.RequestException as exc:
            raise ValueError(f"❌ Échec de la requête API : {exc}") from exc
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"❌ Échec du traitement de l'API : {exc}") from exc
