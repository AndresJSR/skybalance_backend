"""History stack used for undo operations in SkyBalance."""

import copy


class HistoryStack:
    """
    LIFO stack that stores snapshots of the AVL tree root.

    Used to support undo operations (Ctrl+Z).
    Before any mutating action, the current tree root is copied and pushed.
    """

    def __init__(self, max_size=50):
        self.stack = []
        self.max_size = max_size

    # -------------------------------------------------------------
    # Core operations
    # -------------------------------------------------------------

    def push(self, root_node):
        """
        Save a deep copy of the current root.
        If the stack is full, remove the oldest snapshot.
        """
        if len(self.stack) >= self.max_size:
            self.stack.pop(0)

        self.stack.append(copy.deepcopy(root_node))

    def pop(self):
        """
        Remove and return the most recent snapshot.
        Return None if the stack is empty.
        """
        if self.is_empty():
            return None

        return self.stack.pop()

    def peek(self):
        """
        Return the most recent snapshot without removing it.
        Return None if the stack is empty.
        """
        if self.is_empty():
            return None

        return self.stack[-1]

    # -------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------

    def is_empty(self):
        return len(self.stack) == 0

    def size(self):
        return len(self.stack)

    def clear(self):
        self.stack = []