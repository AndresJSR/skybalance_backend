"""Binary Search Tree implementation for SkyBalance."""

from collections import deque


class BST:
    """
    Binary Search Tree ordered by node value.

    In this project, the stored value is usually a Flight object
    wrapped inside a Node.
    """

    def __init__(self):
        self.root = None

    # -------------------------------------------------------------
    # Basic access
    # -------------------------------------------------------------

    def get_root(self):
        return self.root

    # -------------------------------------------------------------
    # Insert
    # -------------------------------------------------------------

    def insert(self, node):
        """
        Insert a node into the BST.
        """
        if self.root is None:
            self.root = node
            return

        self.__insert(self.root, node)

    def __insert(self, current_root, node):
        if node.get_value() == current_root.get_value():
            raise ValueError("El valor ya existe en el árbol.")

        if node.get_value() < current_root.get_value():
            if current_root.get_left_child() is None:
                current_root.set_left_child(node)
                node.set_parent(current_root)
                return

            self.__insert(current_root.get_left_child(), node)
            return

        if current_root.get_right_child() is None:
            current_root.set_right_child(node)
            node.set_parent(current_root)
            return

        self.__insert(current_root.get_right_child(), node)

    # -------------------------------------------------------------
    # Search
    # -------------------------------------------------------------

    def search(self, value):
        """
        Search a node by value.
        Returns the node if found, otherwise None.
        """
        if self.root is None:
            return None

        return self.__search(self.root, value)

    def __search(self, current_root, value):
        if current_root is None:
            return None

        if value == current_root.get_value():
            return current_root

        if value < current_root.get_value():
            return self.__search(current_root.get_left_child(), value)

        return self.__search(current_root.get_right_child(), value)

    # -------------------------------------------------------------
    # Delete
    # -------------------------------------------------------------

    def delete(self, value):
        """
        Delete a node by value.
        """
        if self.root is None:
            return

        node = self.search(value)
        if node is None:
            return

        self.__delete(node)

    def __delete(self, node):
        if node.is_leaf():
            self.__delete_leaf(node)
            return

        if node.has_one_child():
            self.__delete_node_with_one_child(node)
            return

        self.__delete_node_with_two_children(node)

    def __delete_leaf(self, node):
        if node == self.root:
            self.root = None
            return

        parent = node.get_parent()

        if parent.get_left_child() == node:
            parent.set_left_child(None)
        else:
            parent.set_right_child(None)

        node.set_parent(None)

    def __delete_node_with_one_child(self, node):
        if node.get_left_child() is not None:
            child = node.get_left_child()
        else:
            child = node.get_right_child()

        parent = node.get_parent()

        if parent is None:
            self.root = child
            child.set_parent(None)
        else:
            if parent.get_left_child() == node:
                parent.set_left_child(child)
            else:
                parent.set_right_child(child)

            child.set_parent(parent)

        node.set_left_child(None)
        node.set_right_child(None)
        node.set_parent(None)

    def __delete_node_with_two_children(self, node):
        predecessor = self.__get_predecessor(node)
        node.set_value(predecessor.get_value())

        if predecessor.is_leaf():
            self.__delete_leaf(predecessor)
        else:
            self.__delete_node_with_one_child(predecessor)

    def __get_predecessor(self, node):
        current = node.get_left_child()

        while current.get_right_child() is not None:
            current = current.get_right_child()

        return current

    # -------------------------------------------------------------
    # Traversals
    # -------------------------------------------------------------

    def get_breadth_first_list(self):
        """
        Return a breadth-first traversal as a list of values.
        """
        if self.root is None:
            return []

        result = []
        queue = deque([self.root])

        while queue:
            current = queue.popleft()
            result.append(current.get_value())

            if current.get_left_child() is not None:
                queue.append(current.get_left_child())

            if current.get_right_child() is not None:
                queue.append(current.get_right_child())

        return result

    def get_pre_order_list(self):
        result = []
        self.__collect_pre_order(self.root, result)
        return result

    def __collect_pre_order(self, node, result):
        if node is None:
            return

        result.append(node.get_value())
        self.__collect_pre_order(node.get_left_child(), result)
        self.__collect_pre_order(node.get_right_child(), result)

    def get_in_order_list(self):
        result = []
        self.__collect_in_order(self.root, result)
        return result

    def __collect_in_order(self, node, result):
        if node is None:
            return

        self.__collect_in_order(node.get_left_child(), result)
        result.append(node.get_value())
        self.__collect_in_order(node.get_right_child(), result)

    def get_post_order_list(self):
        result = []
        self.__collect_post_order(self.root, result)
        return result

    def __collect_post_order(self, node, result):
        if node is None:
            return

        self.__collect_post_order(node.get_left_child(), result)
        self.__collect_post_order(node.get_right_child(), result)
        result.append(node.get_value())

    # -------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------

    def calculate_height(self, node):
        """
        Return the height of a node.
        Empty node height = -1.
        """
        if node is None:
            return -1

        left_height = self.calculate_height(node.get_left_child())
        right_height = self.calculate_height(node.get_right_child())

        if left_height > right_height:
            return 1 + left_height

        return 1 + right_height

    def count_nodes(self):
        return self.__count_nodes(self.root)

    def __count_nodes(self, node):
        if node is None:
            return 0

        return 1 + self.__count_nodes(node.get_left_child()) + self.__count_nodes(node.get_right_child())

    def count_leaves(self):
        return self.__count_leaves(self.root)

    def __count_leaves(self, node):
        if node is None:
            return 0

        if node.is_leaf():
            return 1

        return self.__count_leaves(node.get_left_child()) + self.__count_leaves(node.get_right_child())

    # -------------------------------------------------------------
    # Print
    # -------------------------------------------------------------

    def print_tree(self):
        """
        Print the tree in ASCII form.
        """
        if self.root is None:
            print("El árbol está vacío.")
            return

        self.__print_tree(self.root, "", True)

    def __print_tree(self, node, prefix, is_left):
        if node is None:
            return

        if node.get_right_child() is not None:
            new_prefix = prefix + ("│   " if is_left else "    ")
            self.__print_tree(node.get_right_child(), new_prefix, False)

        connector = "└── " if is_left else "┌── "
        print(prefix + connector + str(node.get_value()))

        if node.get_left_child() is not None:
            new_prefix = prefix + ("    " if is_left else "│   ")
            self.__print_tree(node.get_left_child(), new_prefix, True)