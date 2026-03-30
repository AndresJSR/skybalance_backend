"""Queue used for pending flight insertions in SkyBalance."""

from collections import deque


class InsertionQueue:
    """
    FIFO queue for scheduled flight insertions.

    Stores pending flight data dictionaries.
    The service layer will later transform each item into a Flight
    and then into a Node before inserting it into the AVL/BST.
    """

    def __init__(self):
        self.queue = deque()

    # -------------------------------------------------------------
    # Core operations
    # -------------------------------------------------------------

    def enqueue(self, flight_data):
        """
        Add a new pending insertion to the end of the queue.
        """
        self.queue.append(flight_data)

    def dequeue(self):
        """
        Remove and return the first pending insertion.
        Return None if the queue is empty.
        """
        if self.is_empty():
            return None

        return self.queue.popleft()

    def peek(self):
        """
        Return the first pending insertion without removing it.
        Return None if the queue is empty.
        """
        if self.is_empty():
            return None

        return self.queue[0]

    # -------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------

    def is_empty(self):
        return len(self.queue) == 0

    def size(self):
        return len(self.queue)

    def clear(self):
        self.queue.clear()

    def to_list(self):
        """
        Return all pending insertions as a normal list.
        Useful for debugging, API responses or UI display.
        """
        return list(self.queue)

    def remove_by_code(self, code):
        """
        Remove the first pending insertion with the given code.

        Returns True if removed, otherwise False.
        """
        for i, flight_data in enumerate(self.queue):
            if str(flight_data.get("codigo", "")) == str(code):
                del self.queue[i]
                return True

        return False