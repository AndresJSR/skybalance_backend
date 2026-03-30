"""Flight model for the SkyBalance system."""

import json


class Flight:
    """
    Represents a flight.

    This class stores:
    - Basic flight data
    - Derived values like final price and rentability
    - Tree-related metadata (depth, height, etc.)
    """

    def __init__(
        self,
        code="",
        origin="",
        destination="",
        departure_time="",
        base_price=0.0,
        final_price=None,
        passengers=0,
        priority=1,
        promotion=False,
        alert=False,
        height=1,
        balance_factor=0,
        depth=0,
        critical_node=False,
        rentability=0.0,
    ):
        # Basic flight data
        self.code = str(code)
        self.origin = str(origin)
        self.destination = str(destination)
        self.departure_time = str(departure_time)
        self.base_price = float(base_price)

        # If final_price is not provided, use base_price
        if final_price is None:
            self.final_price = float(base_price)
        else:
            self.final_price = float(final_price)

        self.passengers = int(passengers)
        self.priority = int(priority)
        self.promotion = bool(promotion)
        self.alert = bool(alert)

        # Tree metadata
        self.height = int(height)
        self.balance_factor = int(balance_factor)
        self.depth = int(depth)
        self.critical_node = bool(critical_node)

        # Business metric
        self.rentability = float(rentability)

    # -------------------------------------------------------------
    # Business logic
    # -------------------------------------------------------------

    def compute_final_price(self, critical_depth):
        """
        If depth > critical_depth, price increases by 25%.
        """
        if self.depth > critical_depth:
            self.critical_node = True
            self.final_price = round(self.base_price * 1.25, 2)
        else:
            self.critical_node = False
            self.final_price = round(self.base_price, 2)

        return self.final_price

    def compute_rentability(self):
        """
        rentability = passengers * final_price
                      - 50 (if promotion)
                      + 100 (if critical node)
        """
        score = self.passengers * self.final_price

        if self.promotion:
            score -= 50.0

        if self.critical_node:
            score += 100.0

        self.rentability = round(score, 2)
        return self.rentability

    # -------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------

    @classmethod
    def from_dict(cls, data):
        """
        Create a Flight from a dictionary.

        Compatible with:
        - Topology JSON
        - Insertion JSON
        """

        return cls(
            code=data.get("codigo", data.get("code", "")),
            origin=data.get("origen", data.get("origin", "")),
            destination=data.get("destino", data.get("destination", "")),
            departure_time=data.get("horaSalida", data.get("departureTime", "")),
            base_price=data.get("precioBase", data.get("basePrice", 0.0)),
            final_price=data.get(
                "precioFinal",
                data.get("finalPrice", data.get("precioBase", data.get("basePrice", 0.0))),
            ),
            passengers=data.get("pasajeros", data.get("passengers", 0)),
            priority=data.get("prioridad", data.get("priority", 1)),
            promotion=data.get("promocion", data.get("promotion", False)),
            alert=data.get("alerta", data.get("alert", False)),
            height=data.get("altura", 1),
            balance_factor=data.get("factorEquilibrio", 0),
            depth=data.get("profundidad", 0),
            critical_node=data.get("nodoCritico", False),
            rentability=data.get("rentabilidad", 0.0),
        )

    def to_dict(self):
        """
        Convert Flight to dictionary using project JSON format.
        """

        return {
            "codigo": self.code,
            "origen": self.origin,
            "destino": self.destination,
            "horaSalida": self.departure_time,
            "precioBase": self.base_price,
            "precioFinal": self.final_price,
            "pasajeros": self.passengers,
            "prioridad": self.priority,
            "promocion": self.promotion,
            "alerta": self.alert,
            "altura": self.height,
            "factorEquilibrio": self.balance_factor,
            "profundidad": self.depth,
            "nodoCritico": self.critical_node,
            "rentabilidad": self.rentability,
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    # -------------------------------------------------------------
    # Comparison (needed for AVL/BST)
    # -------------------------------------------------------------

    def __lt__(self, other):
        return self.code < other.code

    def __gt__(self, other):
        return self.code > other.code

    def __eq__(self, other):
        if isinstance(other, Flight):
            return self.code == other.code
        return False

    # -------------------------------------------------------------
    # Display
    # -------------------------------------------------------------

    def __str__(self):
        return "Flight(code=" + self.code + ", origin=" + self.origin + ", destination=" + self.destination + ")"

    def __repr__(self):
        return self.__str__()