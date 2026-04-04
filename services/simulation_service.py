"""Parallel queue simulation orchestration."""

import threading
import time
import uuid
from datetime import datetime


class SimulationService:
	"""Run and track parallel queue simulations using TreeService-owned state."""

	def __init__(self, tree_service):
		self.tree_service = tree_service

	def start_parallel_queue_simulation(self, workers=2, max_items=None, delay_ms=0):
		workers = int(workers)
		delay_ms = int(delay_ms)

		if workers <= 0:
			return {"error": "El número de workers debe ser mayor que cero."}

		if delay_ms < 0:
			return {"error": "delayMs no puede ser negativo."}

		if max_items is not None:
			max_items = int(max_items)
			if max_items <= 0:
				return {"error": "maxItems debe ser mayor que cero."}

		with self.tree_service.simulation_lock:
			for simulation in self.tree_service.simulations.values():
				if simulation["status"] == "running":
					return {
						"error": "Ya existe una simulación activa.",
						"activeJobId": simulation["jobId"],
					}

		with self.tree_service.queue_lock:
			queue_size = self.tree_service.queue.size()

		if queue_size == 0:
			return {"error": "La cola está vacía."}

		target_total = queue_size if max_items is None else min(queue_size, max_items)
		job_id = str(uuid.uuid4())
		started_at = datetime.utcnow().isoformat() + "Z"

		simulation = {
			"jobId": job_id,
			"status": "running",
			"workers": workers,
			"delayMs": delay_ms,
			"maxItems": max_items,
			"queueSizeAtStart": queue_size,
			"total": target_total,
			"claimed": 0,
			"processed": 0,
			"inserted": 0,
			"failed": 0,
			"warnings": 0,
			"stopRequested": False,
			"startedAt": started_at,
			"endedAt": None,
			"events": [],
		}

		worker_threads = []

		with self.tree_service.simulation_lock:
			self.tree_service.simulations[job_id] = simulation

		for worker_id in range(1, workers + 1):
			thread = threading.Thread(
				target=self._parallel_simulation_worker,
				args=(job_id, worker_id),
				daemon=True,
			)
			thread.start()
			worker_threads.append(thread)

		monitor = threading.Thread(
			target=self._parallel_simulation_monitor,
			args=(job_id, worker_threads),
			daemon=True,
		)
		monitor.start()

		return {
			"jobId": job_id,
			"status": "running",
			"workers": workers,
			"total": target_total,
			"queueSizeAtStart": queue_size,
			"startedAt": started_at,
		}

	def stop_parallel_queue_simulation(self, job_id):
		with self.tree_service.simulation_lock:
			simulation = self.tree_service.simulations.get(job_id)

			if simulation is None:
				return {"error": "La simulación no existe."}

			if simulation["status"] != "running":
				return {
					"error": "La simulación no está en ejecución.",
					"status": simulation["status"],
				}

			simulation["stopRequested"] = True

			return {
				"jobId": job_id,
				"status": simulation["status"],
				"stopRequested": True,
			}

	def get_parallel_simulation_status(self, job_id):
		with self.tree_service.simulation_lock:
			simulation = self.tree_service.simulations.get(job_id)

			if simulation is None:
				return {"error": "La simulación no existe."}

			return self._build_simulation_status(simulation)

	def list_parallel_simulation_events(self, job_id, offset=0, limit=100):
		offset = int(offset)
		limit = int(limit)

		if offset < 0:
			return {"error": "offset no puede ser negativo."}

		if limit <= 0:
			return {"error": "limit debe ser mayor que cero."}

		with self.tree_service.simulation_lock:
			simulation = self.tree_service.simulations.get(job_id)

			if simulation is None:
				return {"error": "La simulación no existe."}

			events = simulation["events"]
			selected = events[offset:offset + limit]

			return {
				"jobId": job_id,
				"status": simulation["status"],
				"offset": offset,
				"limit": limit,
				"totalEvents": len(events),
				"events": selected,
			}

	def _parallel_simulation_worker(self, job_id, worker_id):
		while True:
			with self.tree_service.simulation_lock:
				simulation = self.tree_service.simulations.get(job_id)

				if simulation is None:
					return

				if simulation["stopRequested"]:
					return

				if simulation["claimed"] >= simulation["total"]:
					return

				# Keep claimed reservation before dequeue to preserve current concurrency
				# semantics and avoid workers exceeding the target_total in races.
				simulation["claimed"] += 1
				delay_ms = simulation["delayMs"]

			with self.tree_service.queue_lock:
				flight_data = self.tree_service.queue.dequeue()

			if flight_data is None:
				self._append_simulation_event(
					job_id,
					worker_id,
					None,
					"error",
					"La cola no tenía suficientes elementos para completar la simulación.",
					None,
					None,
				)

				with self.tree_service.simulation_lock:
					simulation = self.tree_service.simulations.get(job_id)
					if simulation is not None:
						simulation["processed"] += 1
						simulation["failed"] += 1
				continue

			code = str(flight_data.get("codigo", ""))

			try:
				with self.tree_service.tree_lock:
					# TODO: migrate this private indirection to a public queue_service API
					# (e.g. queue_service.insert_and_check_conflicts) in a future cleanup.
					insert_result = self.tree_service._insert_and_check_conflicts(
						flight_data
					)
					avl_summary = self.tree_service.get_avl_summary()
					bst_summary = self.tree_service.get_bst_summary()

				conflict = insert_result["conflict"]

				self._append_simulation_event(
					job_id,
					worker_id,
					code,
					"inserted",
					None,
					avl_summary,
					bst_summary,
					conflict=conflict,
				)

				with self.tree_service.simulation_lock:
					simulation = self.tree_service.simulations.get(job_id)
					if simulation is not None:
						simulation["processed"] += 1
						simulation["inserted"] += 1
						if conflict["hasConflict"]:
							simulation["warnings"] += 1

			except ValueError as error:
				self._append_simulation_event(
					job_id,
					worker_id,
					code,
					"error",
					str(error),
					None,
					None,
				)

				with self.tree_service.simulation_lock:
					simulation = self.tree_service.simulations.get(job_id)
					if simulation is not None:
						simulation["processed"] += 1
						simulation["failed"] += 1

			if delay_ms > 0:
				time.sleep(delay_ms / 1000.0)

	def _parallel_simulation_monitor(self, job_id, worker_threads):
		for thread in worker_threads:
			thread.join()

		with self.tree_service.simulation_lock:
			simulation = self.tree_service.simulations.get(job_id)

			if simulation is None:
				return

			simulation["endedAt"] = datetime.utcnow().isoformat() + "Z"

			if simulation["stopRequested"]:
				simulation["status"] = "stopped"
			else:
				simulation["status"] = "completed"

	def _append_simulation_event(
		self,
		job_id,
		worker_id,
		code,
		result,
		message,
		avl_summary,
		bst_summary,
		conflict=None,
	):
		event = {
			"timestamp": datetime.utcnow().isoformat() + "Z",
			"workerId": worker_id,
			"codigo": code,
			"result": result,
			"message": message,
			"avl": avl_summary,
			"bst": bst_summary,
			"conflict": conflict,
		}

		with self.tree_service.simulation_lock:
			simulation = self.tree_service.simulations.get(job_id)
			if simulation is not None:
				simulation["events"].append(event)

	def _build_simulation_status(self, simulation):
		progress = 0.0
		if simulation["total"] > 0:
			progress = round((simulation["processed"] / simulation["total"]) * 100.0, 2)

		return {
			"jobId": simulation["jobId"],
			"status": simulation["status"],
			"workers": simulation["workers"],
			"delayMs": simulation["delayMs"],
			"maxItems": simulation["maxItems"],
			"queueSizeAtStart": simulation["queueSizeAtStart"],
			"total": simulation["total"],
			"claimed": simulation["claimed"],
			"processed": simulation["processed"],
			"inserted": simulation["inserted"],
			"failed": simulation["failed"],
			"warnings": simulation["warnings"],
			"stopRequested": simulation["stopRequested"],
			"startedAt": simulation["startedAt"],
			"endedAt": simulation["endedAt"],
			"progressPercent": progress,
			"lastEvents": simulation["events"][-10:],
		}
