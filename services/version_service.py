"""Version persistence and restore logic for named AVL snapshots."""

import json
import os
import threading

from persistence.json_loader import JsonLoader
from persistence.json_serializer import JsonSerializer


VERSIONS_FILE = os.path.join(os.path.dirname(__file__), "..", "versions_store.json")


class VersionService:
	"""Manage named versions of the AVL tree with disk persistence."""

	def __init__(self):
		self.versions = {}
		self.versions_lock = threading.Lock()
		self._load_versions_from_disk()

	def save_version(self, name, root, critical_depth, load_mode):
		with self.versions_lock:
			self.versions[name] = {
				"snapshot": JsonSerializer.serialize_tree(root),
				"criticalDepth": critical_depth,
				"loadMode": load_mode,
			}
			keys = list(self.versions.keys())

		self._persist_versions_to_disk()

		return {
			"saved": name,
			"versions": keys,
		}

	def restore_version(self, name):
		with self.versions_lock:
			exists = name in self.versions

		if not exists:
			return {"error": "La versión no existe."}

		with self.versions_lock:
			snapshot = self.versions[name]

		if snapshot is None:
			return {"root": None, "criticalDepth": None, "loadMode": None, "hasContext": True}

		if isinstance(snapshot, dict) and "snapshot" in snapshot:
			root_data = snapshot.get("snapshot")
			critical_depth = snapshot.get("criticalDepth")
			load_mode = snapshot.get("loadMode")
			has_context = True
		else:
			# Backward compatibility for legacy versions that only stored the tree.
			root_data = snapshot
			critical_depth = None
			load_mode = None
			has_context = False

		root = JsonLoader.build_topology_tree(root_data, None, 0)
		return {
			"root": root,
			"criticalDepth": critical_depth,
			"loadMode": load_mode,
			"hasContext": has_context,
		}

	def restore_version_root(self, name):
		"""Backward-compatible alias for existing callers."""
		return self.restore_version(name)

	def list_versions(self):
		with self.versions_lock:
			return list(self.versions.keys())

	def delete_version(self, name):
		with self.versions_lock:
			if name not in self.versions:
				return {"error": "La versión no existe."}

			del self.versions[name]
			keys = list(self.versions.keys())

		self._persist_versions_to_disk()

		return {
			"deleted": name,
			"versions": keys,
		}

	def _load_versions_from_disk(self):
		"""
		Load saved versions from disk into memory on service startup.
		Silently ignores missing or corrupt files.
		"""
		path = os.path.abspath(VERSIONS_FILE)

		if not os.path.isfile(path):
			return

		try:
			with open(path, "r", encoding="utf-8") as fh:
				data = json.load(fh)

			if isinstance(data, dict):
				with self.versions_lock:
					self.versions = data

		except (OSError, json.JSONDecodeError):
			pass

	def _persist_versions_to_disk(self):
		"""
		Write all current versions to disk atomically.
		Uses a .tmp file + rename to avoid partial writes.
		"""
		path = os.path.abspath(VERSIONS_FILE)
		tmp_path = path + ".tmp"

		with self.versions_lock:
			snapshot = dict(self.versions)

		try:
			with open(tmp_path, "w", encoding="utf-8") as fh:
				json.dump(snapshot, fh, ensure_ascii=False, indent=2)

			os.replace(tmp_path, path)

		except OSError:
			pass
