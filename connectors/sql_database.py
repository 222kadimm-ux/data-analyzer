"""Read-only SQL table loader with identifier validation and bounded results."""
from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse

import pandas as pd
import polars as pl
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from .base import BaseConnector


def _validate_db_url(db_url: str) -> None:
    if not isinstance(db_url, str) or not db_url.strip():
        raise ValueError("URL de base de données obligatoire.")
    try:
        parsed = make_url(db_url)
    except Exception as exc:
        raise ValueError("URL de base de données invalide.") from exc
    if parsed.drivername.split("+")[0] not in {"postgresql", "mysql", "mariadb", "sqlite"}:
        raise ValueError("Type de base de données non pris en charge.")
    if parsed.drivername.split("+")[0] != "sqlite":
        if not parsed.host:
            raise ValueError("L'hôte de la base de données est manquant.")
        # In hosted deployments, configure SQL_ALLOWED_HOSTS with comma-separated
        # hostnames. This is strongly recommended to prevent server-side request forgery.
        allowlist = {h.strip().lower() for h in os.getenv("SQL_ALLOWED_HOSTS", "").split(",") if h.strip()}
        if allowlist and parsed.host.lower() not in allowlist:
            raise ValueError("Hôte SQL non autorisé par la configuration du serveur.")
        if parsed.host.lower() in {"localhost", "localhost.localdomain"}:
            raise ValueError("Les connexions locales doivent être explicitement autorisées par l'administrateur.")
        try:
            ip = ipaddress.ip_address(parsed.host)
            if (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved) and parsed.host.lower() not in allowlist:
                raise ValueError("Adresse IP privée/non publique non autorisée sans configuration explicite.")
        except ValueError as exc:
            if "non autorisée" in str(exc) or "non autorisé" in str(exc):
                raise
            # Host is a DNS name, not an IP literal.


class SQLDatabaseConnector(BaseConnector):
    def __init__(self, db_url: str, table_name: str, limit: int = 10000):
        self.db_url = db_url
        self.table_name = (table_name or "").strip()
        try:
            self.limit = int(limit)
        except (TypeError, ValueError):
            self.limit = 10000
        self.limit = max(1, min(self.limit, 10000))

    def load_data(self) -> pl.DataFrame:
        _validate_db_url(self.db_url)
        if not self.table_name or len(self.table_name) > 256 or any(ch in self.table_name for ch in ";\x00\n\r"):
            raise ValueError("Nom de table invalide.")
        # Support a simple schema.table form; never interpolate a raw identifier.
        parts = self.table_name.split(".")
        if len(parts) not in (1, 2) or any(not p or not (p.replace("_", "").isalnum()) for p in parts):
            raise ValueError("Nom de table invalide. Utilisez table ou schema.table.")

        engine = None
        try:
            engine = create_engine(self.db_url, pool_pre_ping=True, pool_recycle=300)
            inspector = inspect(engine)
            schema, table = (parts[0], parts[1]) if len(parts) == 2 else (None, parts[0])
            if table not in inspector.get_table_names(schema=schema):
                raise ValueError("La table demandée n'existe pas ou n'est pas accessible.")
            preparer = engine.dialect.identifier_preparer
            quoted_table = preparer.quote(table)
            if schema:
                quoted_table = f"{preparer.quote_schema(schema)}.{quoted_table}"
            query = text(f"SELECT * FROM {quoted_table} LIMIT :row_limit")
            with engine.connect() as connection:
                # Bound parameter protects the row limit; table identifier was quoted.
                result = connection.execute(query, {"row_limit": self.limit})
                df_pd = pd.DataFrame(result.fetchall(), columns=result.keys())
            return pl.from_pandas(df_pd)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError(f"Échec de lecture SQL. Vérifiez l'URL, les droits en lecture et le nom de table ({type(exc).__name__}).") from exc
        finally:
            if engine is not None:
                engine.dispose()


def validate_simple_select(sql: str, expected_table: str) -> str:
    """Allow only a single-table SELECT generated for the selected table.

    This intentionally rejects advanced SQL (joins, CTEs, subqueries, comments,
    multiple statements). Use a database account with SELECT-only permissions too.
    """
    import re
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("Requête SQL vide.")
    query = sql.strip()
    if query.endswith(";"):
        query = query[:-1].rstrip()
    if ";" in query or "--" in query or "/*" in query or "*/" in query or "#" in query:
        raise ValueError("Commentaires et requêtes multiples interdits.")
    if not re.match(r"(?is)^select\s+", query):
        raise ValueError("Seules les requêtes SELECT sont autorisées.")
    if re.search(r"(?i)\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|execute|call|copy|into|union|intersect|except|join|with|information_schema|pg_catalog)\b", query):
        raise ValueError("La requête contient une opération ou une structure interdite.")
    if re.search(r"(?i)\bselect\b", query[6:]):
        raise ValueError("Les sous-requêtes ne sont pas autorisées.")
    parts = expected_table.split(".")
    if len(parts) not in (1, 2) or any(not part or not part.replace("_", "").isalnum() for part in parts):
        raise ValueError("Nom de table sélectionné invalide.")
    table_pattern = r"(?i)\bfrom\s+[\"`]?" + re.escape(parts[-1]) + r"[\"`]?\b"
    matches = list(re.finditer(r"(?i)\bfrom\s+([\w\"`.]+)", query))
    if len(matches) != 1:
        raise ValueError("La requête doit lire une seule table.")
    actual = matches[0].group(1).replace('"', '').replace('`', '')
    # Accept either the exact schema.table name or the table component when
    # the SQL dialect omits schema qualification in the generated query.
    actual_parts = actual.split(".")
    expected_parts = expected_table.split(".")
    if actual.lower() != expected_table.lower():
        if len(expected_parts) == 2 and len(actual_parts) == 1 and actual_parts[0].lower() == expected_parts[-1].lower():
            pass
        else:
            raise ValueError("La requête doit utiliser uniquement la table sélectionnée.")
    if re.search(r"(?i)\b(limit|fetch|top)\b", query) is None:
        query += " LIMIT 1000"
    else:
        limit_match = re.search(r"(?i)\blimit\s+(\d+)", query)
        if limit_match and int(limit_match.group(1)) > 1000:
            query = query[:limit_match.start(1)] + "1000" + query[limit_match.end(1):]
        elif not limit_match:
            raise ValueError("Utilisez LIMIT numérique (maximum 1000) dans la requête.")
    return query
