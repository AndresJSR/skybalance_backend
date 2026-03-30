"""JSON serializer for SkyBalance trees."""

import json


class JsonSerializer:
    """
    Serializes the real tree structure to JSON.

    The output format preserves:
    - current node data
    - left subtree as 'izquierdo'
    - right subtree as 'derecho'

    This matches the project requirement of exporting the real hierarchy
    of the tree, not just a flat list of flights.
    """

    @staticmethod
    def serialize_tree(root_node):
        """
        Serialize the full tree starting from the root node.
        Returns a dictionary (or None if the tree is empty).
        """
        return JsonSerializer.serialize_node(root_node)

    @staticmethod
    def serialize_node(node):
        """
        Serialize one node and its children recursively.

        Returns:
        - None if node is None
        - dict with flight data + izquierdo + derecho otherwise
        """
        if node is None:
            return None

        flight = node.get_value()
        data = flight.to_dict()

        data["izquierdo"] = JsonSerializer.serialize_node(node.get_left_child())
        data["derecho"] = JsonSerializer.serialize_node(node.get_right_child())

        return data

    @staticmethod
    def to_json_text(root_node):
        """
        Convert the tree to formatted JSON text.
        """
        data = JsonSerializer.serialize_tree(root_node)
        return json.dumps(data, indent=2, ensure_ascii=False)

    @staticmethod
    def to_json_bytes(root_node):
        """
        Convert the tree to UTF-8 encoded JSON bytes.
        Useful for file download or saving.
        """
        json_text = JsonSerializer.to_json_text(root_node)
        return json_text.encode("utf-8")