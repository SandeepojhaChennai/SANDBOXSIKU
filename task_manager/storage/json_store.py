"""JSON file-based storage backend for persisting application data."""

import json
import os
from typing import Dict, List, Optional


class JsonStore:
    """Simple JSON file storage for all application entities."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._collections: Dict[str, Dict[str, dict]] = {}

    def _file_path(self, collection: str) -> str:
        return os.path.join(self.data_dir, f"{collection}.json")

    def _load(self, collection: str) -> Dict[str, dict]:
        if collection in self._collections:
            return self._collections[collection]
        path = self._file_path(collection)
        if os.path.exists(path):
            with open(path, "r") as f:
                self._collections[collection] = json.load(f)
        else:
            self._collections[collection] = {}
        return self._collections[collection]

    def _save(self, collection: str) -> None:
        path = self._file_path(collection)
        with open(path, "w") as f:
            json.dump(self._collections.get(collection, {}), f, indent=2)

    def insert(self, collection: str, id: str, data: dict) -> dict:
        """Insert a new record into a collection."""
        records = self._load(collection)
        if id in records:
            raise ValueError(f"Record with id '{id}' already exists in '{collection}'")
        records[id] = data
        self._save(collection)
        return data

    def get(self, collection: str, id: str) -> Optional[dict]:
        """Get a single record by ID."""
        records = self._load(collection)
        return records.get(id)

    def get_all(self, collection: str) -> List[dict]:
        """Get all records in a collection."""
        records = self._load(collection)
        return list(records.values())

    def update(self, collection: str, id: str, data: dict) -> dict:
        """Update an existing record."""
        records = self._load(collection)
        if id not in records:
            raise ValueError(f"Record with id '{id}' not found in '{collection}'")
        records[id] = data
        self._save(collection)
        return data

    def delete(self, collection: str, id: str) -> bool:
        """Delete a record by ID."""
        records = self._load(collection)
        if id not in records:
            return False
        del records[id]
        self._save(collection)
        return True

    def find(self, collection: str, **filters) -> List[dict]:
        """Find records matching all provided field filters."""
        records = self._load(collection)
        results = []
        for record in records.values():
            match = all(record.get(k) == v for k, v in filters.items())
            if match:
                results.append(record)
        return results
