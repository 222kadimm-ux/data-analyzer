"""Synchronous facade for a short, self-contained OPC UA read session.

asyncua is asynchronous, so all client operations run on one event loop. This
avoids creating a client on one loop and using it from another Streamlit rerun.
"""
from __future__ import annotations

import asyncio
import math
import time
from typing import Any
from urllib.parse import urlparse

from asyncua import Client


class OPCUAConnector:
    def __init__(self, url: str, node_id: str, timeout: float = 10.0):
        self.url = (url or "").strip()
        self.node_id = (node_id or "").strip()
        self.timeout = max(1.0, min(float(timeout), 60.0))

    def _validate(self) -> None:
        parsed = urlparse(self.url)
        if parsed.scheme != "opc.tcp" or not parsed.hostname or not parsed.port:
            raise ValueError("Adresse OPC UA invalide. Format attendu : opc.tcp://hôte:port")
        if not self.node_id:
            raise ValueError("Node ID obligatoire.")

    async def _session(self, duration_sec: float, interval_sec: float) -> tuple[Any, list[dict], str]:
        self._validate()
        duration_sec = max(0.0, min(float(duration_sec), 300.0))
        interval_sec = max(0.2, min(float(interval_sec), 30.0))
        client = Client(url=self.url, timeout=self.timeout)
        data: list[dict] = []
        last_value = None
        try:
            await asyncio.wait_for(client.connect(), timeout=self.timeout)
            node = client.get_node(self.node_id)
            # Always make at least one read, including when duration is zero.
            end_at = time.monotonic() + duration_sec
            while True:
                try:
                    value = await asyncio.wait_for(node.read_value(), timeout=self.timeout)
                    last_value = value
                    data.append({"timestamp": time.time(), "value": value})
                except Exception as exc:
                    return last_value, data, f"Erreur de lecture OPC UA : {exc}"
                if time.monotonic() >= end_at:
                    break
                await asyncio.sleep(min(interval_sec, max(0.0, end_at - time.monotonic())))
            return last_value, data, "Connexion et lecture terminées."
        except Exception as exc:
            return None, data, f"Connexion OPC UA impossible : {exc}"
        finally:
            try:
                await asyncio.wait_for(client.disconnect(), timeout=self.timeout)
            except Exception:
                pass

    def run_session(self, duration_sec: float = 0, interval_sec: float = 1) -> tuple[Any, list[dict], str]:
        """Connect, read/stream, and disconnect within a single asyncio loop."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self._session(duration_sec, interval_sec))
        raise RuntimeError("run_session doit être appelé depuis un contexte synchrone.")

    # Compatibility helpers for code that only needs one connection/read cycle.
    def connect(self):
        value, data, status = self.run_session(0, 1)
        if data:
            return True, status
        return False, status

    def read_value(self):
        value, data, status = self.run_session(0, 1)
        return (value, "✅") if data else (None, status)

    def disconnect(self):
        # Sessions are always disconnected in run_session's finally block.
        return None

    def start_streaming(self, duration_sec=10, interval_sec=1):
        _, data, status = self.run_session(duration_sec, interval_sec)
        if not data and status != "Connexion et lecture terminées.":
            raise RuntimeError(status)
        return data
