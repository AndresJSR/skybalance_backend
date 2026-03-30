"""Node class used by BST and AVL trees."""


class Node:
    """
    Generic binary tree node.

    This node stores:
    - a value (for this project, usually a Flight)
    - parent reference
    - left child reference
    - right child reference

    The same Node class is used for both BST and AVL.
    """

    def __init__(self, value):
        self.value = value
        self.parent = None
        self.left_child = None
        self.right_child = None

    # -------------------------------------------------------------
    # Value
    # -------------------------------------------------------------

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    # -------------------------------------------------------------
    # Parent
    # -------------------------------------------------------------

    def get_parent(self):
        return self.parent

    def set_parent(self, parent_node):
        self.parent = parent_node

    # -------------------------------------------------------------
    # Left child
    # -------------------------------------------------------------

    def get_left_child(self):
        return self.left_child

    def set_left_child(self, left_child_node):
        self.left_child = left_child_node

    # -------------------------------------------------------------
    # Right child
    # -------------------------------------------------------------

    def get_right_child(self):
        return self.right_child

    def set_right_child(self, right_child_node):
        self.right_child = right_child_node

    # -------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------

    def is_leaf(self):
        return self.left_child is None and self.right_child is None

    def has_left_child(self):
        return self.left_child is not None

    def has_right_child(self):
        return self.right_child is not None

    def has_one_child(self):
        return (
            (self.left_child is not None and self.right_child is None)
            or
            (self.left_child is None and self.right_child is not None)
        )

    def has_two_children(self):
        return self.left_child is not None and self.right_child is not None

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return "Node(value=" + str(self.value) + ")"