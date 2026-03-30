"""Main application service for the SkyBalance backend."""

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

        snapshot = self.versions[name]
        if snapshot is None:
            self.avl.root = None
        else:
            self.avl.root = JsonLoader.build_topology_tree(snapshot, None, 0)

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
        self.queue.enqueue(flight_data)
        return {
            "queued": self.queue.size(),
            "pending": self.queue.to_list()
        }

    def process_next_in_queue(self):
        flight_data = self.queue.dequeue()

        if flight_data is None:
            return {"error": "La cola está vacía."}

        result = self.insert_flight(flight_data)
        result["inserted"] = flight_data
        result["remaining"] = self.queue.size()
        return result

    def process_full_queue(self):
        inserted_codes = []

        while not self.queue.is_empty():
            flight_data = self.queue.dequeue()
            self.insert_flight(flight_data)
            inserted_codes.append(str(flight_data.get("codigo", "")))

        response = self.get_tree_response()
        response["insertedCodes"] = inserted_codes
        return response

    def list_queue(self):
        return {
            "size": self.queue.size(),
            "pending": self.queue.to_list()
        }

    def remove_from_queue(self, code):
        removed = self.queue.remove_by_code(code)

        if not removed:
            return {"error": "Ese vuelo no está en la cola."}

        return {
            "removed": code,
            "remaining": self.queue.size()
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