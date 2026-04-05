"""Queue orchestration and conflict-aware insertion helpers."""

from models.flight import Flight


class QueueService:
	"""Manage insertion queue operations while TreeService keeps ownership of state."""

	def __init__(self, tree_service):
		self.tree_service = tree_service

	def enqueue_flight(self, flight_data):
		with self.tree_service.queue_lock:
			self.tree_service.queue.enqueue(flight_data)
			pending = self.tree_service.queue.to_list()

		return {
			"queued": len(pending),
			"pending": pending,
		}

	def process_next_in_queue(self):
		with self.tree_service.queue_lock:
			flight_data = self.tree_service.queue.dequeue()

		if flight_data is None:
			return {"error": "La cola está vacía."}

		with self.tree_service.tree_lock:
			result = self._insert_and_check_conflicts(flight_data)

		with self.tree_service.queue_lock:
			remaining = self.tree_service.queue.size()

		result["inserted"] = flight_data
		result["remaining"] = remaining
		return result

	def process_full_queue(self):
		inserted_codes = []
		conflicts = []

		while True:
			with self.tree_service.queue_lock:
				if self.tree_service.queue.is_empty():
					break

				flight_data = self.tree_service.queue.dequeue()

			with self.tree_service.tree_lock:
				insert_result = self._insert_and_check_conflicts(flight_data)

			code = str(flight_data.get("codigo", ""))
			inserted_codes.append(code)

			if insert_result["conflict"]["hasConflict"]:
				conflicts.append({
					"codigo": code,
					"types": insert_result["conflict"]["types"],
					"rotationDelta": insert_result["conflict"]["rotationDelta"],
					"criticalDepth": insert_result["conflict"]["criticalDepth"],
					"rotationTriggered": insert_result["conflict"]["rotationTriggered"],
				})

		response = self.tree_service.get_tree_response()
		response["insertedCodes"] = inserted_codes
		response["conflicts"] = conflicts
		return response

	def list_queue(self):
		with self.tree_service.queue_lock:
			size = self.tree_service.queue.size()
			pending = self.tree_service.queue.to_list()

		return {
			"size": size,
			"pending": pending,
		}

	def remove_from_queue(self, code):
		with self.tree_service.queue_lock:
			removed = self.tree_service.queue.remove_by_code(code)
			remaining = self.tree_service.queue.size()

		if not removed:
			return {"error": "Ese vuelo no está en la cola."}

		return {
			"removed": code,
			"remaining": remaining,
		}

	def _insert_and_check_conflicts(self, flight_data):
		"""
		Insert a flight and return the tree response enriched with a conflict report.

		Conflict types detected:
		- critical_depth: inserted node lands beyond the critical depth threshold.
		- rotation_triggered: insertion caused at least one AVL rotation.
		"""
		before_rotations = dict(self.tree_service.avl.get_rotation_stats())

		result = self.tree_service.insert_flight(flight_data)

		after_rotations = dict(self.tree_service.avl.get_rotation_stats())

		rotation_delta = {
			k: after_rotations[k] - before_rotations[k]
			for k in before_rotations
		}
		rotation_triggered = any(v > 0 for v in rotation_delta.values())

		key = Flight.from_dict({"codigo": flight_data.get("codigo", "")})
		inserted_node = self.tree_service.avl.search(key)
		critical_depth_hit = (
			inserted_node is not None and inserted_node.get_value().critical_node
		)

		conflict_types = []
		if critical_depth_hit:
			conflict_types.append("critical_depth")
		if rotation_triggered:
			conflict_types.append("rotation_triggered")

		result["conflict"] = {
			"hasConflict": len(conflict_types) > 0,
			"types": conflict_types,
			"rotationDelta": rotation_delta,
			"criticalDepth": critical_depth_hit,
			"rotationTriggered": rotation_triggered,
		}
		return result