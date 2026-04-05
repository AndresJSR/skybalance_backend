"""AVL Tree implementation for SkyBalance."""

from collections import deque
from structures.node import Node


class AVL:
    """
    Self-balancing binary search tree.

    Stores Node objects whose values are usually Flight objects.
    """

    def __init__(self):
        self.root = None
        self.stress_mode = False
        self.rotation_count = {
            "LL": 0,
            "RR": 0,
            "LR": 0,
            "RL": 0
        }
        self.mass_cancellations = 0

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
        Insert a node into the AVL tree.
        Rebalance automatically unless stress mode is enabled.
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

                if not self.stress_mode:
                    self.__check_balance(node)
                return

            self.__insert(current_root.get_left_child(), node)
            return

        if current_root.get_right_child() is None:
            current_root.set_right_child(node)
            node.set_parent(current_root)

            if not self.stress_mode:
                self.__check_balance(node)
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
        Delete one node by value.
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

        if not self.stress_mode:
            self.__check_balance(parent)

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

        if parent is not None and not self.stress_mode:
            self.__check_balance(parent)

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
    # Cancel subtree
    # -------------------------------------------------------------

    def cancel(self, value):
        """
        Remove a node and its entire subtree.
        Returns the number of removed nodes.
        """
        if self.root is None:
            return 0

        node = self.search(value)
        if node is None:
            return 0

        removed_count = self.__count_subtree(node)
        self.mass_cancellations += 1

        parent = node.get_parent()

        if parent is None:
            self.root = None
        else:
            if parent.get_left_child() == node:
                parent.set_left_child(None)
            else:
                parent.set_right_child(None)

        node.set_parent(None)

        if parent is not None and not self.stress_mode:
            self.__check_balance(parent)

        return removed_count

    # -------------------------------------------------------------
    # Traversals
    # -------------------------------------------------------------

    def get_breadth_first_list(self):
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
        Return height of node.
        Empty node height = -1.
        """
        if node is None:
            return -1

        left_height = self.calculate_height(node.get_left_child())
        right_height = self.calculate_height(node.get_right_child())

        return 1 + max(left_height, right_height)

    def get_balance_factor(self, node):
        """
        Balance factor = left subtree height - right subtree height
        """
        if node is None:
            return 0

        left_height = self.calculate_height(node.get_left_child())
        right_height = self.calculate_height(node.get_right_child())
        return left_height - right_height

    def count_nodes(self):
        return self.__count_subtree(self.root)

    def __count_subtree(self, node):
        if node is None:
            return 0

        return 1 + self.__count_subtree(node.get_left_child()) + self.__count_subtree(node.get_right_child())

    def count_leaves(self):
        return self.__count_leaves(self.root)

    def __count_leaves(self, node):
        if node is None:
            return 0

        if node.is_leaf():
            return 1

        return self.__count_leaves(node.get_left_child()) + self.__count_leaves(node.get_right_child())

    def get_rotation_stats(self):
        return dict(self.rotation_count)

    # -------------------------------------------------------------
    # Stress mode
    # -------------------------------------------------------------

    def enable_stress_mode(self):
        self.stress_mode = True

    def disable_stress_mode(self):
        self.stress_mode = False

    # -------------------------------------------------------------
    # Global rebalance
    # -------------------------------------------------------------

    def global_rebalance(self):
        """
        Rebalance the current tree in place by cascading local rotations.
        Detects unbalanced nodes explicitly while traversing the tree.
        """
        before = dict(self.rotation_count)
        stats = {
            "unbalancedNodesDetected": 0,
        }

        self.root = self.__rebalance_subtree(self.root, stats)
        self.stress_mode = False

        after = dict(self.rotation_count)
        rotations_applied = {
            "LL": after["LL"] - before["LL"],
            "RR": after["RR"] - before["RR"],
            "LR": after["LR"] - before["LR"],
            "RL": after["RL"] - before["RL"]
        }

        return {
            "LL": rotations_applied["LL"],
            "RR": rotations_applied["RR"],
            "LR": rotations_applied["LR"],
            "RL": rotations_applied["RL"],
            "unbalancedNodesDetected": stats["unbalancedNodesDetected"],
            "totalRotations": (
                rotations_applied["LL"]
                + rotations_applied["RR"]
                + rotations_applied["LR"]
                + rotations_applied["RL"]
            ),
            "strategy": "cascading-rotations"
        }

    def __rebalance_subtree(self, node, stats):
        """
        Rebalance subtree bottom-up so rotations cascade naturally.
        Returns the new root of this subtree.
        """
        if node is None:
            return None

        left = self.__rebalance_subtree(node.get_left_child(), stats)
        right = self.__rebalance_subtree(node.get_right_child(), stats)

        node.set_left_child(left)
        if left is not None:
            left.set_parent(node)

        node.set_right_child(right)
        if right is not None:
            right.set_parent(node)

        detected_here = False

        while True:
            balance_factor = self.get_balance_factor(node)

            if -1 <= balance_factor <= 1:
                break

            if not detected_here:
                stats["unbalancedNodesDetected"] += 1
                detected_here = True

            case = self.__identify_rebalance_case(node, balance_factor)

            if case == "LL":
                node = self.__rotate_right_local(node)
                self.rotation_count["LL"] += 1
                continue

            if case == "RR":
                node = self.__rotate_left_local(node)
                self.rotation_count["RR"] += 1
                continue

            if case == "LR":
                rotated_left = self.__rotate_left_local(node.get_left_child())
                node.set_left_child(rotated_left)
                rotated_left.set_parent(node)
                node = self.__rotate_right_local(node)
                self.rotation_count["LR"] += 1
                continue

            rotated_right = self.__rotate_right_local(node.get_right_child())
            node.set_right_child(rotated_right)
            rotated_right.set_parent(node)
            node = self.__rotate_left_local(node)
            self.rotation_count["RL"] += 1

        return node

    def __rotate_left_local(self, top_node):
        """Rotate subtree left and return its new root."""
        middle_node = top_node.get_right_child()
        transfer_subtree = middle_node.get_left_child()

        middle_node.set_left_child(top_node)
        top_node.set_parent(middle_node)

        top_node.set_right_child(transfer_subtree)
        if transfer_subtree is not None:
            transfer_subtree.set_parent(top_node)

        middle_node.set_parent(None)
        return middle_node

    def __rotate_right_local(self, top_node):
        """Rotate subtree right and return its new root."""
        middle_node = top_node.get_left_child()
        transfer_subtree = middle_node.get_right_child()

        middle_node.set_right_child(top_node)
        top_node.set_parent(middle_node)

        top_node.set_left_child(transfer_subtree)
        if transfer_subtree is not None:
            transfer_subtree.set_parent(top_node)

        middle_node.set_parent(None)
        return middle_node

    # -------------------------------------------------------------
    # AVL audit
    # -------------------------------------------------------------

    def audit_avl(self):
        """
        Verify AVL property and metadata consistency in all nodes.
        Returns a report.
        """
        issues = []
        self.__audit(self.root, issues)

        return {
            "valid": len(issues) == 0,
            "totalNodes": self.count_nodes(),
            "inconsistentNodes": issues
        }

    def __audit(self, node, issues):
        if node is None:
            return

        flight = node.get_value()
        calculated_height = self.calculate_height(node)
        calculated_balance_factor = self.get_balance_factor(node)

        stored_height = getattr(flight, "height", None)
        # Backward-compatible lookup for legacy naming.
        stored_balance_factor = getattr(
            flight,
            "balance_factor",
            getattr(flight, "balanceFactor", None),
        )

        is_structurally_unbalanced = (
            calculated_balance_factor < -1 or calculated_balance_factor > 1
        )
        missing_height_metadata = stored_height is None
        missing_balance_metadata = stored_balance_factor is None
        has_height_mismatch = (
            not missing_height_metadata and stored_height != calculated_height
        )
        has_balance_mismatch = (
            not missing_balance_metadata
            and stored_balance_factor != calculated_balance_factor
        )

        if (
            is_structurally_unbalanced
            or missing_height_metadata
            or missing_balance_metadata
            or has_height_mismatch
            or has_balance_mismatch
        ):
            issue = {
                "code": flight.get_code(),
                "balanceFactor": calculated_balance_factor,
                "height": calculated_height,
            }

            if missing_height_metadata:
                issue["missingStoredHeight"] = True

            if missing_balance_metadata:
                issue["missingStoredBalanceFactor"] = True

            if has_height_mismatch:
                issue["storedHeight"] = stored_height

            if has_balance_mismatch:
                issue["storedBalanceFactor"] = stored_balance_factor

            issues.append(issue)

        self.__audit(node.get_left_child(), issues)
        self.__audit(node.get_right_child(), issues)

    # -------------------------------------------------------------
    # Rebalancing
    # -------------------------------------------------------------

    def __check_balance(self, node):
        if node is None:
            return

        balance_factor = self.get_balance_factor(node)

        if balance_factor > 1 or balance_factor < -1:
            self.__rebalance(node, balance_factor)

        self.__check_balance(node.get_parent())

    def __rebalance(self, node, balance_factor):
        case = self.__identify_rebalance_case(node, balance_factor)

        if case == "LL":
            self.__balance_ll(node)
            self.rotation_count["LL"] += 1
            return

        if case == "RR":
            self.__balance_rr(node)
            self.rotation_count["RR"] += 1
            return

        if case == "LR":
            self.__balance_lr(node)
            self.rotation_count["LR"] += 1
            return

        if case == "RL":
            self.__balance_rl(node)
            self.rotation_count["RL"] += 1

    def __identify_rebalance_case(self, node, balance_factor):
        if balance_factor > 0:
            child_balance = self.get_balance_factor(node.get_left_child())

            if child_balance >= 0:
                return "LL"

            return "LR"

        child_balance = self.get_balance_factor(node.get_right_child())

        if child_balance > 0:
            return "RL"

        return "RR"

    def __balance_ll(self, top_node):
        middle_node = top_node.get_left_child()
        parent = top_node.get_parent()
        right_subtree = middle_node.get_right_child()

        middle_node.set_right_child(top_node)
        top_node.set_parent(middle_node)

        middle_node.set_parent(parent)

        if parent is None:
            self.root = middle_node
        else:
            if parent.get_left_child() == top_node:
                parent.set_left_child(middle_node)
            else:
                parent.set_right_child(middle_node)

        top_node.set_left_child(right_subtree)

        if right_subtree is not None:
            right_subtree.set_parent(top_node)

    def __balance_rr(self, top_node):
        middle_node = top_node.get_right_child()
        parent = top_node.get_parent()
        left_subtree = middle_node.get_left_child()

        middle_node.set_left_child(top_node)
        top_node.set_parent(middle_node)

        middle_node.set_parent(parent)

        if parent is None:
            self.root = middle_node
        else:
            if parent.get_left_child() == top_node:
                parent.set_left_child(middle_node)
            else:
                parent.set_right_child(middle_node)

        top_node.set_right_child(left_subtree)

        if left_subtree is not None:
            left_subtree.set_parent(top_node)

    def __balance_lr(self, top_node):
        middle_node = top_node.get_left_child()
        self.__balance_rr(middle_node)
        self.__balance_ll(top_node)

    def __balance_rl(self, top_node):
        middle_node = top_node.get_right_child()
        self.__balance_ll(middle_node)
        self.__balance_rr(top_node)

    # -------------------------------------------------------------
    # Print
    # -------------------------------------------------------------

    def print_tree(self):
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