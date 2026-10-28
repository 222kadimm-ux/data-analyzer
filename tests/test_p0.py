import pandas as pd
import database


class FakeCursor:
    def __init__(self):
        self.calls = []
    def execute(self, query, params=None):
        self.calls.append((query, params))
    def close(self):
        pass

class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False
    def cursor(self):
        return self.cursor_obj
    def commit(self):
        self.committed = True
    def close(self):
        pass


def test_save_anonymous_user_without_real_database(monkeypatch):
    conn = FakeConnection()
    monkeypatch.setattr(database, "get_db_connection", lambda: conn)
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    assert database.save_file("test-uuid-1234", "test.csv", df) is True
    assert conn.committed is True
    query, params = conn.cursor_obj.calls[0]
    assert "INSERT INTO user_files" in query
    assert params[0] == "test-uuid-1234"


def test_date_format_roundtrip():
    df = pd.DataFrame({"date": pd.to_datetime(["2026-10-27"])})
    json_data = df.to_json(orient="records", date_format="iso")
    assert "2026-10-27" in json_data
