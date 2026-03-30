"""JSON loader for SkyBalance."""

import json

from models.flight import Flight
from structures.node import Node


class JsonLoader:
    """
    Loads JSON files for the SkyBalance system.

    Supported modes:
    - TOPOLOGIA: builds the exact tree structure from nested 'izquierdo'/'derecho'
    - INSERCION: returns the list of flights to be inserted one by one
    """

    @staticmethod
    def load(raw_bytes):
        """
        Load raw JSON bytes and detect the mode automatically.

        Returns a dictionary with one of these formats:

        For topology:
        {
            "mode": "TOPOLOGIA",
            "root": <Node or None>
        }

        For insertion:
        {
            "mode": "INSERCION",
            "ordering": "codigo",
            "flights": [dict, dict, ...]
        }
        """
        try:
            data = json.loads(raw_bytes)
        except Exception:
            raise ValueError("El archivo JSON no es válido.")

        mode = JsonLoader.detect_mode(data)

        if mode == "TOPOLOGIA":
            root = JsonLoader.build_topology_tree(data, None, 0)
            return {
                "mode": "TOPOLOGIA",
                "root": root
            }

        if mode == "INSERCION":
            flights = data.get("vuelos", [])

            if not isinstance(flights, list):
                raise ValueError("El campo 'vuelos' debe ser una lista.")

            return {
                "mode": "INSERCION",
                "ordering": data.get("ordenamiento", "codigo"),
                "flights": flights
            }

        raise ValueError("No se pudo determinar el modo del JSON.")

    @staticmethod
    def detect_mode(data):
        """
        Detect whether the JSON is TOPOLOGIA or INSERCION.
        """
        if not isinstance(data, dict):
            raise ValueError("El contenido del JSON debe ser un objeto.")

        if str(data.get("tipo", "")).upper() == "INSERCION":
            return "INSERCION"

        if "codigo" in data and ("izquierdo" in data or "derecho" in data):
            return "TOPOLOGIA"

        return None

    @staticmethod
    def build_topology_tree(data, parent_node=None, depth=0):
        """
        Recursively build a tree of Node objects from topology JSON.
        """
        if data is None:
            return None

        flight = Flight.from_dict(data)
        flight.set_depth(depth)

        node = Node(flight)
        node.set_parent(parent_node)

        left_child = JsonLoader.build_topology_tree(
            data.get("izquierdo"),
            node,
            depth + 1
        )

        right_child = JsonLoader.build_topology_tree(
            data.get("derecho"),
            node,
            depth + 1
        )

        node.set_left_child(left_child)
        node.set_right_child(right_child)

        return node