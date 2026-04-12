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
from services.audit_service import AuditService
from services.metrics_service import MetricsService
from services.pricing_service import PricingService
from services.queue_service import QueueService
from services.simulation_service import SimulationService
from services.version_service import VersionService


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
        self.audit_service = AuditService()
        self.metrics_service = MetricsService()
        self.pricing_service = PricingService()
        self.queue_service = QueueService(self)
        self.simulation_service = SimulationService(self)
        self.version_service = VersionService()
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
        # Versions are persistent named snapshots managed explicitly by the user.
        # They survive loading a new JSON file and server restarts.
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

        if self.load_mode == "INSERCION":
            self.bst.insert(Node(Flight.from_dict(flight_data)))

        self.recalculate_all_metadata()
        return self.get_tree_response()

    def _insert_and_check_conflicts(self, flight_data):
        return self.queue_service._insert_and_check_conflicts(flight_data)

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
        self._rebuild_bst_from_avl()
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
        self._rebuild_bst_from_avl()
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
        self._rebuild_bst_from_avl()
        return self.get_tree_response()

    # -------------------------------------------------------------
    # Versions
    # -------------------------------------------------------------

    def save_version(self, name):
        return self.version_service.save_version(name, self.avl.get_root())

    def restore_version(self, name):
        self.save_history()
        restore_result = self.version_service.restore_version(name)

        if "error" in restore_result:
            return restore_result

        self.avl.root = restore_result["root"]

        self.recalculate_all_metadata()
        self._rebuild_bst_from_avl()
        response = self.get_tree_response()
        response["restored"] = name
        return response

    def _rebuild_bst_from_avl(self):
        """
        Rebuild BST from current AVL inorder traversal.
        Keeps BST consistent after operations that only mutate AVL.
        """
        self.bst = BST()

        if self.load_mode != "INSERCION":
            return

        for flight in self.avl.get_in_order_list():
            self.bst.insert(Node(Flight.from_dict(flight.to_dict())))

    def list_versions(self):
        return self.version_service.list_versions()

    def delete_version(self, name):
        return self.version_service.delete_version(name)

    # -------------------------------------------------------------
    # Queue
    # -------------------------------------------------------------

    def enqueue_flight(self, flight_data):
        return self.queue_service.enqueue_flight(flight_data)

    def process_next_in_queue(self):
        return self.queue_service.process_next_in_queue()

    def process_full_queue(self):
        return self.queue_service.process_full_queue()

    def list_queue(self):
        return self.queue_service.list_queue()

    def remove_from_queue(self, code):
        return self.queue_service.remove_from_queue(code)

    def start_parallel_queue_simulation(self, workers=2, max_items=None, delay_ms=0):
        return self.simulation_service.start_parallel_queue_simulation(
            workers,
            max_items,
            delay_ms,
        )

    def stop_parallel_queue_simulation(self, job_id):
        return self.simulation_service.stop_parallel_queue_simulation(job_id)

    def get_parallel_simulation_status(self, job_id):
        return self.simulation_service.get_parallel_simulation_status(job_id)

    def list_parallel_simulation_events(self, job_id, offset=0, limit=100):
        return self.simulation_service.list_parallel_simulation_events(
            job_id,
            offset,
            limit,
        )

    def _parallel_simulation_worker(self, job_id, worker_id):
        return self.simulation_service._parallel_simulation_worker(job_id, worker_id)

    def _parallel_simulation_monitor(self, job_id, worker_threads):
        return self.simulation_service._parallel_simulation_monitor(
            job_id,
            worker_threads,
        )

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
        return self.simulation_service._append_simulation_event(
            job_id,
            worker_id,
            code,
            result,
            message,
            avl_summary,
            bst_summary,
            conflict=conflict,
        )

    def _build_simulation_status(self, simulation):
        return self.simulation_service._build_simulation_status(simulation)

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
        return self.audit_service.enable_stress_mode(self.avl)

    def disable_stress_mode(self):
        return self.audit_service.disable_stress_mode(self.avl)

    def audit_avl(self):
        return self.audit_service.audit_avl(self.avl)

    def global_rebalance(self):
        self.save_history()
        rotation_stats = self.audit_service.global_rebalance(self.avl)

        if isinstance(rotation_stats, dict) and "error" in rotation_stats:
            return rotation_stats

        self.avl.disable_stress_mode()
        self.recalculate_all_metadata()

        response = self.get_tree_response()
        response["rotationsApplied"] = rotation_stats
        response["stressMode"] = False
        return response

    # -------------------------------------------------------------
    # Critical depth / business values
    # -------------------------------------------------------------

    def set_critical_depth(self, depth):
        set_result = self.pricing_service.set_critical_depth(
            self.avl,
            depth,
        )

        if isinstance(set_result, dict) and "error" in set_result:
            return set_result

        self.critical_depth = set_result

        response = self.get_tree_response()
        response["criticalDepth"] = self.critical_depth
        return response

    def eliminate_least_profitable(self):
        target_result = self.pricing_service.eliminate_least_profitable(self.avl)

        if "error" in target_result:
            return target_result

        code = target_result["code"]
        rentability = target_result["rentability"]

        result = self.cancel_flight(code)
        result["cancelledCode"] = code
        result["rentability"] = rentability
        return result

    def find_least_profitable_node(self):
        return self.pricing_service.find_least_profitable_node(self.avl)

    def collect_rentability(self, node, result):
        return self.pricing_service.collect_rentability(node, result)

    # -------------------------------------------------------------
    # Metrics / summaries
    # -------------------------------------------------------------

    def get_metrics(self):
        return self.metrics_service.get_metrics(self.avl, self.critical_depth)

    def get_avl_summary(self):
        return self.metrics_service.get_avl_summary(self.avl)

    def get_bst_summary(self):
        return self.metrics_service.get_bst_summary(self.bst)

    def get_tree_response(self):
        return self.metrics_service.get_tree_response(self.avl)

    def get_comparative_snapshot(self):
        """
        Return the current AVL/BST comparative snapshot.

        In TOPOLOGIA mode (or before any load), BST is not part of the
        active comparison and is returned as None.
        """
        is_insertion_mode = self.load_mode == "INSERCION"

        return {
            "mode": self.load_mode,
            "avl": self.get_avl_summary(),
            "bst": self.get_bst_summary() if is_insertion_mode else None,
            "avlTree": JsonSerializer.serialize_tree(self.avl.get_root()),
            "bstTree": (
                JsonSerializer.serialize_tree(self.bst.get_root())
                if is_insertion_mode
                else None
            ),
        }

    # -------------------------------------------------------------
    # Metadata recalculation
    # -------------------------------------------------------------

    def recalculate_all_metadata(self):
        self.pricing_service.recalculate_all_metadata(self.avl, self.critical_depth)

    def recalculate_metadata_from_node(self, node, depth):
        self.pricing_service.recalculate_metadata_from_node(
            self.avl,
            node,
            depth,
            self.critical_depth,
        )