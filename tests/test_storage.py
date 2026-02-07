"""Tests for the JSON storage backend."""

import shutil
import tempfile

import pytest

from task_manager.storage.json_store import JsonStore


@pytest.fixture
def store():
    tmp_dir = tempfile.mkdtemp()
    s = JsonStore(data_dir=tmp_dir)
    yield s
    shutil.rmtree(tmp_dir)


class TestJsonStore:
    def test_insert_and_get(self, store):
        data = {"id": "1", "name": "test"}
        store.insert("items", "1", data)
        result = store.get("items", "1")
        assert result == data

    def test_insert_duplicate_raises(self, store):
        store.insert("items", "1", {"id": "1"})
        with pytest.raises(ValueError, match="already exists"):
            store.insert("items", "1", {"id": "1"})

    def test_get_nonexistent(self, store):
        assert store.get("items", "999") is None

    def test_get_all(self, store):
        store.insert("items", "1", {"id": "1", "name": "a"})
        store.insert("items", "2", {"id": "2", "name": "b"})
        all_items = store.get_all("items")
        assert len(all_items) == 2

    def test_update(self, store):
        store.insert("items", "1", {"id": "1", "name": "old"})
        store.update("items", "1", {"id": "1", "name": "new"})
        result = store.get("items", "1")
        assert result["name"] == "new"

    def test_update_nonexistent_raises(self, store):
        with pytest.raises(ValueError, match="not found"):
            store.update("items", "999", {"id": "999"})

    def test_delete(self, store):
        store.insert("items", "1", {"id": "1"})
        assert store.delete("items", "1") is True
        assert store.get("items", "1") is None

    def test_delete_nonexistent(self, store):
        assert store.delete("items", "999") is False

    def test_find_with_filters(self, store):
        store.insert("items", "1", {"id": "1", "type": "a", "color": "red"})
        store.insert("items", "2", {"id": "2", "type": "b", "color": "red"})
        store.insert("items", "3", {"id": "3", "type": "a", "color": "blue"})
        results = store.find("items", type="a")
        assert len(results) == 2
        results = store.find("items", type="a", color="red")
        assert len(results) == 1

    def test_persistence(self, store):
        """Data persists across loads by clearing the cache."""
        store.insert("items", "1", {"id": "1", "name": "persisted"})
        # Clear in-memory cache to force re-read from disk
        store._collections.clear()
        result = store.get("items", "1")
        assert result["name"] == "persisted"
