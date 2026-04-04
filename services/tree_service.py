"""Main application service for the SkyBalance backend."""

import threading
import time
import uuid
from datetime import datetime

from models.flight import Flight
from structures.node import Node
from structures.avl_tree import AVL
from structures.bst_tree import BST
from structures.history_stack import HistoryStack
from structures.insertion_queue import InsertionQueue
from persistence.json_loader import JsonLoader
from persistence.json_serializer import JsonSerializer


class TreeService:
    """
    Main orchestrator of the system.

    Responsibilities:
    - Load trees from JSON
    - Manage AVL/BST operations
    - Handle undo history
    - Handle insertion queue
    - Handle named versions
    - Export current AVL tree to JSON
    - Recalculate metadata and business values after mutations
    """

    def __init__(self):
        self.avl = AVL()
        self.bst = BST()
        self.history = HistoryStack(max_size=50)
        self.queue = InsertionQueue()
        self.versions = {}
        self.load_mode = None
        self.critical_depth = 999
        self.queue_lock = threading.Lock()
        self.tree_lock = threading.Lock()
        self.simulation_lock = threading.Lock()
        self.simulations = {}

    # -------------------------------------------------------------
    # Load / reset
    # -------------------------------------------------------------

    def reset_all(self):
        self.avl = AVL()
        self.bst = BST()
        self.history.clear()
        self.queue.clear()
        self.versions.clear()
        self.load_mode = None
        self.critical_depth = 999

    def load_json(self, raw_bytes, critical_depth=999):
        """
        Load a JSON file in either TOPOLOGIA or INSERCION mode.
        """
        self.reset_all()
        self.critical_depth = critical_depth

        result = JsonLoader.load(raw_bytes)
        self.load_mode = result["mode"]

        if result["mode"] == "TOPOLOGIA":
            self.avl.root = result["root"]
            self.recalculate_all_metadata()
            return {
                "mode": "TOPOLOGIA",
                "avl": self.get_avl_summary(),
                "bst": None,
                "avlTree": JsonSerializer.serialize_tree(self.avl.get_root()),
                "bstTree": None,
            }

        if result["mode"] == "INSERCION":
            flights = result["flights"]

            for flight_data in flights:
                avl_flight = Flight.from_dict(flight_data)
                bst_flight = Flight.from_dict(flight_data)

                self.avl.insert(Node(avl_flight))
                self.bst.insert(Node(bst_flight))

            self.recalculate_all_metadata()

            return {
                "mode": "INSERCION",
                "ordering": result["ordering"],
                "avl": self.get_avl_summary(),
                "bst": self.get_bst_summary(),
                "avlTree": JsonSerializer.serialize_tree(self.avl.get_root()),
                "bstTree": JsonSerializer.serialize_tree(self.bst.get_root()),
            }

        raise ValueError("Modo de carga no soportado.")

    # -------------------------------------------------------------
    # CRUD
    # -------------------------------------------------------------

    def insert_flight(self, flight_data):
        self.save_history()

        flight = Flight.from_dict(flight_data)
        self.avl.insert(Node(flight))
        self.bst.insert(Node(Flight.from_dict(flight_data)))
        self.recalculate_all_metadata()
        return self.get_tree_response()

    def _insert_and_check_conflicts(self, flight_data):
        """
        Insert a flight and return the tree response enriched with a conflict report.

        Conflict types detected:
        - critical_depth: inserted node lands beyond the critical depth threshold.
        - rotation_triggered: insertion caused at least one AVL rotation.
        """
        before_rotations = dict(self.avl.get_rotation_stats())

        self.save_history()
        flight = Flight.from_dict(flight_data)
        self.avl.insert(Node(flight))
        self.bst.insert(Node(Flight.from_dict(flight_data)))
        self.recalculate_all_metadata()

        after_rotations = dict(self.avl.get_rotation_stats())

        rotation_delta = {
            k: after_rotations[k] - before_rotations[k]
            for k in before_rotations
        }
        rotation_triggered = any(v > 0 for v in rotation_delta.values())

        key = Flight.from_dict({"codigo": flight_data.get("codigo", "")})
        inserted_node = self.avl.search(key)
        critical_depth_hit = (
            inserted_node is not None and inserted_node.get_value().critical_node
        )

        conflict_types = []
        if critical_depth_hit:
            conflict_types.append("critical_depth")
        if rotation_triggered:
            conflict_types.append("rotation_triggered")

        result = self.get_tree_response()
        result["conflict"] = {
            "hasConflict": len(conflict_types) > 0,
            "types": conflict_types,
            "rotationDelta": rotation_delta,
            "criticalDepth": critical_depth_hit,
            "rotationTriggered": rotation_triggered,
        }
        return result

    def update_flight(self, code, updates):
        key = Flight.from_dict({"codigo": code})
        node = self.avl.search(key)

        if node is None:
            return {"error": "Vuelo no encontrado."}

        self.save_history()
        flight = node.get_value()

        if "origen" in updates:
            flight.origin = str(updates["origen"])
        if "destino" in updates:
            flight.destination = str(updates["destino"])
        if "horaSalida" in updates:
            flight.departure_time = str(updates["horaSalida"])
        if "precioBase" in updates:
            flight.base_price = float(updates["precioBase"])
        if "pasajeros" in updates:
            flight.passengers = int(updates["pasajeros"])
        if "prioridad" in updates:
            flight.priority = int(updates["prioridad"])
        if "promocion" in updates:
            flight.promotion = bool(updates["promocion"])
        if "alerta" in updates:
            flight.alert = bool(updates["alerta"])

        self.recalculate_all_metadata()
        return self.get_tree_response()

    def delete_flight(self, code):
        key = Flight.from_dict({"codigo": code})
        node = self.avl.search(key)

        if node is None:
            return {"error": "Vuelo no encontrado."}

        self.save_history()
        self.avl.delete(key)
        self.bst.delete(key)
        self.recalculate_all_metadata()
        return self.get_tree_response()

    def cancel_flight(self, code):
        key = Flight.from_dict({"codigo": code})
        node = self.avl.search(key)

        if node is None:
            return {"error": "Vuelo no encontrado."}

        self.save_history()
        removed = self.avl.cancel(key)

        self.recalculate_all_metadata()
        response = self.get_tree_response()
        response["nodesRemoved"] = removed
        return response

    def search_flight(self, code):
        key = Flight.from_dict({"codigo": code})
        node = self.avl.search(key)

        if node is None:
            return {"error": "Vuelo no encontrado."}

        return node.get_value().to_dict()

    # -------------------------------------------------------------
    # Undo
    # -------------------------------------------------------------

    def save_history(self):
        self.history.push(self.avl.get_root())

    def undo(self):
        previous_root = self.history.pop()

        if previous_root is None:
            return {"error": "No hay acciones para deshacer."}

        self.avl.root = previous_root
        self.recalculate_all_metadata()
        return self.get_tree_response()

    # -------------------------------------------------------------
    # Versions
    # -------------------------------------------------------------

    def save_version(self, name):
        self.versions[name] = JsonSerializer.serialize_tree(self.avl.get_root())
        return {
            "saved": name,
            "versions": list(self.versions.keys())
        }

    def restore_version(self, name):
        if name not in self.versions:
            return {"error": "La versión no existe."}

        self.save_history()

        if self.versions[name] is None:
            self.avl.root = None
        else:
            self.avl.root = JsonLoader.build_topology_tree(self.versions[name], None, 0)

        self.recalculate_all_metadata()
        response = self.get_tree_response()
        response["restored"] = name
        return response

    def list_versions(self):
        return list(self.versions.keys())

    def delete_version(self, name):
        if name not in self.versions:
            return {"error": "La versión no existe."}

        del self.versions[name]
        return {
            "deleted": name,
            "versions": list(self.versions.keys())
        }

    # -------------------------------------------------------------
    # Queue
    # -------------------------------------------------------------

    def enqueue_flight(self, flight_data):
        with self.queue_lock:
            self.queue.enqueue(flight_data)
            pending = self.queue.to_list()

        return {
            "queued": len(pending),
            "pending": pending
        }

    def process_next_in_queue(self):
        with self.queue_lock:
            flight_data = self.queue.dequeue()

        if flight_data is None:
            return {"error": "La cola está vacía."}

        with self.tree_lock:
            result = self._insert_and_check_conflicts(flight_data)

        with self.queue_lock:
            remaining = self.queue.size()

        result["inserted"] = flight_data
        result["remaining"] = remaining
        return result

    def process_full_queue(self):
        inserted_codes = []
        conflicts = []

        while True:
            with self.queue_lock:
                if self.queue.is_empty():
                    break

                flight_data = self.queue.dequeue()

            with self.tree_lock:
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

        response = self.get_tree_response()
        response["insertedCodes"] = inserted_codes
        response["conflicts"] = conflicts
        return response

    def list_queue(self):
        with self.queue_lock:
            size = self.queue.size()
            pending = self.queue.to_list()

        return {
            "size": size,
            "pending": pending
        }

    def remove_from_queue(self, code):
        with self.queue_lock:
            removed = self.queue.remove_by_code(code)
            remaining = self.queue.size()

        if not removed:
            return {"error": "Ese vuelo no está en la cola."}

        return {
            "removed": code,
            "remaining": remaining
        }

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

        with self.simulation_lock:
            for simulation in self.simulations.values():
                if simulation["status"] == "running":
                    return {
                        "error": "Ya existe una simulación activa.",
                        "activeJobId": simulation["jobId"],
                    }

        with self.queue_lock:
            queue_size = self.queue.size()

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

        with self.simulation_lock:
            self.simulations[job_id] = simulation

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
        with self.simulation_lock:
            simulation = self.simulations.get(job_id)

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
        with self.simulation_lock:
            simulation = self.simulations.get(job_id)

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

        with self.simulation_lock:
            simulation = self.simulations.get(job_id)

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
            with self.simulation_lock:
                simulation = self.simulations.get(job_id)

                if simulation is None:
                    return

                if simulation["stopRequested"]:
                    return

                if simulation["claimed"] >= simulation["total"]:
                    return

                simulation["claimed"] += 1
                delay_ms = simulation["delayMs"]

            with self.queue_lock:
                flight_data = self.queue.dequeue()

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

                with self.simulation_lock:
                    simulation = self.simulations.get(job_id)
                    if simulation is not None:
                        simulation["processed"] += 1
                        simulation["failed"] += 1
                continue

            code = str(flight_data.get("codigo", ""))

            try:
                with self.tree_lock:
                    insert_result = self._insert_and_check_conflicts(flight_data)
                    avl_summary = self.get_avl_summary()
                    bst_summary = self.get_bst_summary()

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

                with self.simulation_lock:
                    simulation = self.simulations.get(job_id)
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

                with self.simulation_lock:
                    simulation = self.simulations.get(job_id)
                    if simulation is not None:
                        simulation["processed"] += 1
                        simulation["failed"] += 1

            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

    def _parallel_simulation_monitor(self, job_id, worker_threads):
        for thread in worker_threads:
            thread.join()

        with self.simulation_lock:
            simulation = self.simulations.get(job_id)

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

        with self.simulation_lock:
            simulation = self.simulations.get(job_id)
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

    # -------------------------------------------------------------
    # Export
    # -------------------------------------------------------------

    def export_json_bytes(self):
        return JsonSerializer.to_json_bytes(self.avl.get_root())

    def export_json_text(self):
        return JsonSerializer.to_json_text(self.avl.get_root())

    # -------------------------------------------------------------
    # Stress mode / audit / rebalance
    # -------------------------------------------------------------

    def enable_stress_mode(self):
        self.avl.enable_stress_mode()
        return {"stressMode": True}

    def disable_stress_mode(self):
        self.avl.disable_stress_mode()
        return {"stressMode": False}

    def audit_avl(self):
        if not self.avl.stress_mode:
            return {"error": "La auditoría solo está disponible en modo estrés."}

        return self.avl.audit_avl()

    def global_rebalance(self):
        self.save_history()
        rotation_stats = self.avl.global_rebalance()
        self.recalculate_all_metadata()

        response = self.get_tree_response()
        response["rotationsApplied"] = rotation_stats
        response["stressMode"] = False
        return response

    # -------------------------------------------------------------
    # Critical depth / business values
    # -------------------------------------------------------------

    def set_critical_depth(self, depth):
        self.critical_depth = int(depth)
        self.recalculate_all_metadata()

        response = self.get_tree_response()
        response["criticalDepth"] = self.critical_depth
        return response

    def eliminate_least_profitable(self):
        if self.avl.get_root() is None:
            return {"error": "El árbol está vacío."}

        target = self.find_least_profitable_node()
        if target is None:
            return {"error": "No se encontró un nodo candidato."}

        code = target.get_value().get_code()
        rentability = target.get_value().rentability

        result = self.cancel_flight(code)
        result["cancelledCode"] = code
        result["rentability"] = rentability
        return result

    def find_least_profitable_node(self):
        candidates = []
        self.collect_rentability(self.avl.get_root(), candidates)

        if len(candidates) == 0:
            return None

        best = candidates[0]

        for candidate in candidates[1:]:
            if candidate[0] < best[0]:
                best = candidate
            elif candidate[0] == best[0]:
                if candidate[1] > best[1]:
                    best = candidate
                elif candidate[1] == best[1]:
                    if candidate[2] > best[2]:
                        best = candidate

        return best[3]

    def collect_rentability(self, node, result):
        if node is None:
            return

        flight = node.get_value()
        result.append((
            flight.rentability,
            flight.depth,
            flight.code,
            node
        ))

        self.collect_rentability(node.get_left_child(), result)
        self.collect_rentability(node.get_right_child(), result)

    # -------------------------------------------------------------
    # Metrics / summaries
    # -------------------------------------------------------------

    def get_metrics(self):
        root = self.avl.get_root()
        has_root = root is not None

        return {
            "height": self.avl.calculate_height(root) + 1 if has_root else 0,
            "totalNodes": self.avl.count_nodes(),
            "leafCount": self.avl.count_leaves(),
            "rotations": self.avl.get_rotation_stats(),
            "massCancellations": self.avl.mass_cancellations,
            "stressMode": self.avl.stress_mode,
            "criticalDepth": self.critical_depth,
            "bfs": [flight.to_dict() for flight in self.avl.get_breadth_first_list()],
            "dfs": [flight.to_dict() for flight in self.avl.get_pre_order_list()],
            "inorder": [flight.to_dict() for flight in self.avl.get_in_order_list()],
        }

    def get_avl_summary(self):
        root = self.avl.get_root()

        return {
            "raiz": root.get_value().get_code() if root is not None else None,
            "profundidad": self.avl.calculate_height(root) + 1 if root is not None else 0,
            "cantidadHojas": self.avl.count_leaves(),
            "totalNodos": self.avl.count_nodes(),
            "rotaciones": self.avl.get_rotation_stats(),
        }

    def get_bst_summary(self):
        root = self.bst.get_root()

        return {
            "raiz": root.get_value().get_code() if root is not None else None,
            "profundidad": self.bst.calculate_height(root) + 1 if root is not None else 0,
            "cantidadHojas": self.bst.count_leaves(),
            "totalNodos": self.bst.count_nodes(),
        }

    def get_tree_response(self):
        return {
            "tree": JsonSerializer.serialize_tree(self.avl.get_root()),
            "properties": self.get_avl_summary()
        }

    # -------------------------------------------------------------
    # Metadata recalculation
    # -------------------------------------------------------------

    def recalculate_all_metadata(self):
        self.recalculate_metadata_from_node(self.avl.get_root(), 0)

    def recalculate_metadata_from_node(self, node, depth):
        if node is None:
            return

        flight = node.get_value()

        flight.depth = depth
        flight.height = self.avl.calculate_height(node)
        flight.balance_factor = self.avl.get_balance_factor(node)

        flight.compute_final_price(self.critical_depth)
        flight.compute_rentability()

        self.recalculate_metadata_from_node(node.get_left_child(), depth + 1)
        self.recalculate_metadata_from_node(node.get_right_child(), depth + 1)