"""Flight routes for the SkyBalance API."""

from flask import Blueprint, request
from routes import service, success_response, error_response

flights_bp = Blueprint("flights", __name__, url_prefix="/api")


@flights_bp.route("/flights", methods=["GET"])
def list_flights():
    """
    List all current flights in the AVL tree.
    Returned order: breadth-first traversal (BFS).
    """
    try:
        flights = service.avl.get_breadth_first_list()
        flights_data = [flight.to_dict() for flight in flights]

        return success_response({
            "total": len(flights_data),
            "flights": flights_data
        }, 200)

    except Exception as e:
        return error_response("Error al listar vuelos: " + str(e), 500)


@flights_bp.route("/flights", methods=["POST"])
def create_flight():
    """
    Create a new flight and insert it into the AVL tree.
    """
    try:
        data = request.get_json()

        if not data:
            return error_response("Body vacío o inválido.", 400)

        result = service.insert_flight(data)

        if "error" in result:
            return error_response(result["error"], 400)

        return success_response(result, 201)

    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response("Error al crear vuelo: " + str(e), 500)


@flights_bp.route("/flights/<code>", methods=["GET"])
def get_flight(code):
    """
    Get one flight by code.
    """
    try:
        result = service.search_flight(code)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al buscar vuelo: " + str(e), 500)


@flights_bp.route("/flights/<code>", methods=["PUT"])
def update_flight(code):
    """
    Update an existing flight.

    Body may contain only the fields to modify.
    """
    try:
        data = request.get_json()

        if not data:
            return error_response("Body vacío o inválido.", 400)

        result = service.update_flight(code, data)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except ValueError as e:
        return error_response(str(e), 400)

    except Exception as e:
        return error_response("Error al actualizar vuelo: " + str(e), 500)


@flights_bp.route("/flights/<code>", methods=["DELETE"])
def delete_flight(code):
    """
    Delete one flight node only.
    Does not delete descendants.
    """
    try:
        result = service.delete_flight(code)

        if "error" in result:
            return error_response(result["error"], 404)

        return success_response(result, 200)

    except Exception as e:
        return error_response("Error al eliminar vuelo: " + str(e), 500)