"""
Unit tests for src.database module.

Goal: increase coverage of lazy engine/session initialization and error handling.
"""

import os
import pytest

import src.database as db_module


class TestDatabaseModule:
    def teardown_method(self):
        """Reset lazy globals between tests."""
        db_module._engine = None
        db_module.SessionLocal = None

    def test_database_get_database_url_missing_returns_empty(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        assert db_module.get_database_url() == ""

    def test_database_get_engine_raises_when_database_url_missing(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValueError, match="DATABASE_URL environment variable is not set"):
            db_module.get_engine()

    def test_database_get_engine_uses_env_database_url(self, monkeypatch):
        # Use SQLite URL so this is self-contained
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
        engine = db_module.get_engine()
        assert engine is not None
        assert engine.url is not None
        assert str(engine.url) == "sqlite:///:memory:"

    def test_database_get_db_initializes_sessionlocal_lazily(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

        gen = db_module.get_db()
        session = next(gen)

        try:
            assert db_module.SessionLocal is not None
            assert db_module._engine is not None
            # A live session should have a bind/connection
            assert session.bind is not None
        finally:
            # Close generator to run finally: db.close()
            gen.close()

    def test_database_get_db_reuses_existing_sessionlocal(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

        gen1 = db_module.get_db()
        s1 = next(gen1)
        try:
            sessionlocal_id = id(db_module.SessionLocal)
        finally:
            gen1.close()

        gen2 = db_module.get_db()
        s2 = next(gen2)
        try:
            assert id(db_module.SessionLocal) == sessionlocal_id
        finally:
            gen2.close()
